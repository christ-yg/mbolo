from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from .email_verification import (
    ExpiredEmailVerificationToken,
    InvalidEmailVerificationToken,
    read_email_verification_token,
)
from .models import User
from .legal import (
    CURRENT_PRIVACY_VERSION,
    CURRENT_TERMS_VERSION,
)


class CurrentUserSerializer(serializers.ModelSerializer):
    """Données minimales de l'utilisateur connecté."""

    class Meta:
        model = User

        fields = (
            "id",
            "email",
            "is_email_verified",
            "email_2fa_enabled",
            "is_phone_verified",
            "created_at",
        )

        read_only_fields = fields


class RegistrationSerializer(serializers.Serializer):
    """Validation et création d'un compte."""

    email = serializers.EmailField(
        max_length=254,
        write_only=True,
    )

    password = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    password_confirmation = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    accept_terms = serializers.BooleanField(
        write_only=True,
    )

    confirm_adult = serializers.BooleanField(
        write_only=True,
    )

    def validate_email(
        self,
        value: str,
    ) -> str:
        return (
            User.objects.normalize_email(value)
            .strip()
            .lower()
        )

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        password = attrs["password"]

        if not attrs["accept_terms"]:
            raise serializers.ValidationError(
                {"accept_terms": "Tu dois accepter les documents légaux."}
            )

        if not attrs["confirm_adult"]:
            raise serializers.ValidationError(
                {"confirm_adult": "Mbolo est réservé aux personnes majeures."}
            )

        if password != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {
                    "password_confirmation": (
                        "Les deux mots de passe "
                        "ne correspondent pas."
                    )
                }
            )

        temporary_user = User(
            email=attrs["email"],
        )

        try:
            validate_password(
                password,
                user=temporary_user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": list(exc.messages)}
            ) from exc

        return attrs

    @transaction.atomic
    def create(
        self,
        validated_data: dict[str, Any],
    ) -> User:
        validated_data.pop(
            "password_confirmation",
        )
        validated_data.pop("accept_terms")
        validated_data.pop("confirm_adult")

        try:
            return User.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
                is_email_verified=False,
                is_phone_verified=False,
                terms_accepted_at=timezone.now(),
                terms_version=CURRENT_TERMS_VERSION,
                privacy_version=CURRENT_PRIVACY_VERSION,
            )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Impossible de créer le compte "
                        "avec les informations fournies."
                    )
                }
            ) from exc


class LoginSerializer(serializers.Serializer):
    """Validation sécurisée des identifiants."""

    email = serializers.EmailField(
        max_length=254,
        write_only=True,
    )

    password = serializers.CharField(
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    failure_reason = "invalid_credentials"

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        request = self.context.get("request")

        email = (
            User.objects.normalize_email(
                attrs["email"]
            )
            .strip()
            .lower()
        )

        user = authenticate(
            request=request,
            email=email,
            password=attrs["password"],
        )

        if user is None:
            self.failure_reason = "invalid_credentials"

            raise serializers.ValidationError(
                {
                    "detail": (
                        "Adresse e-mail ou "
                        "mot de passe incorrect."
                    )
                }
            )

        if not user.is_active:
            self.failure_reason = "account_inactive"

            raise serializers.ValidationError(
                {
                    "detail": (
                        "Ce compte ne peut pas être utilisé."
                    )
                }
            )

        if (
            user.is_suspended
            and user.suspension_until is not None
            and user.suspension_until <= timezone.now()
        ):
            user.is_suspended = False
            user.suspension_until = None
            user.save(
                update_fields=(
                    "is_suspended",
                    "suspension_until",
                    "updated_at",
                )
            )

        if user.is_suspended:
            self.failure_reason = "account_suspended"

            raise serializers.ValidationError(
                {
                    "detail": (
                        "Ce compte ne peut pas être utilisé."
                    )
                }
            )

        attrs["email"] = email
        attrs["user"] = user

        return attrs


class EmailVerificationRequestSerializer(
    serializers.Serializer
):
    """
    Valide une demande de nouvel e-mail de vérification.
    """

    email = serializers.EmailField(
        max_length=254,
        write_only=True,
    )

    def validate_email(
        self,
        value: str,
    ) -> str:
        return (
            User.objects.normalize_email(value)
            .strip()
            .lower()
        )


class EmailVerificationConfirmSerializer(
    serializers.Serializer
):
    """
    Valide le jeton puis retrouve le compte correspondant.
    """

    token = serializers.CharField(
        max_length=2048,
        write_only=True,
        trim_whitespace=True,
    )

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            payload = read_email_verification_token(
                attrs["token"]
            )
        except ExpiredEmailVerificationToken as exc:
            raise serializers.ValidationError(
                {
                    "token": (
                        "Le lien de vérification a expiré."
                    )
                }
            ) from exc
        except InvalidEmailVerificationToken as exc:
            raise serializers.ValidationError(
                {
                    "token": (
                        "Le lien de vérification est invalide."
                    )
                }
            ) from exc

        try:
            user = User.objects.get(
                id=payload.user_id,
                email=payload.email,
            )
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                {
                    "token": (
                        "Le lien de vérification est invalide."
                    )
                }
            ) from exc

        attrs["user"] = user

        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254, write_only=True)

    def validate_email(self, value: str) -> str:
        return User.objects.normalize_email(value).strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=256, write_only=True)
    password = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password_confirmation = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {"password_confirmation": "Les deux mots de passe ne correspondent pas."}
            )

        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError(
                {"detail": "Ce lien de réinitialisation est invalide ou a expiré."}
            ) from exc

        if (
            not user.is_active
            or user.is_suspended
            or not default_token_generator.check_token(user, attrs["token"])
        ):
            raise serializers.ValidationError(
                {"detail": "Ce lien de réinitialisation est invalide ou a expiré."}
            )

        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": list(exc.messages)}
            ) from exc

        attrs["user"] = user
        return attrs


class CurrentPasswordSerializer(serializers.Serializer):
    """Exige une nouvelle authentification avant une action sensible."""

    current_password = serializers.CharField(
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Le mot de passe actuel est incorrect."
            )
        return value


class ChangePasswordSerializer(CurrentPasswordSerializer):
    new_password = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    new_password_confirmation = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if (
            attrs["new_password"]
            != attrs["new_password_confirmation"]
        ):
            raise serializers.ValidationError(
                {
                    "new_password_confirmation": (
                        "Les deux nouveaux mots de passe "
                        "ne correspondent pas."
                    )
                }
            )

        user = self.context["request"].user
        if user.check_password(attrs["new_password"]):
            raise serializers.ValidationError(
                {
                    "new_password": (
                        "Le nouveau mot de passe doit être différent."
                    )
                }
            )

        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"new_password": list(exc.messages)}
            ) from exc

        return attrs


class DeactivateAccountSerializer(CurrentPasswordSerializer):
    confirmation = serializers.CharField(
        max_length=32,
        write_only=True,
        trim_whitespace=True,
    )

    def validate_confirmation(self, value: str) -> str:
        if value != "DESACTIVER":
            raise serializers.ValidationError(
                "Écris exactement DESACTIVER pour confirmer."
            )
        return value


class DeleteAccountSerializer(CurrentPasswordSerializer):
    confirmation = serializers.CharField(
        max_length=64,
        write_only=True,
        trim_whitespace=True,
    )

    def validate_confirmation(self, value: str) -> str:
        if value != "SUPPRIMER DEFINITIVEMENT":
            raise serializers.ValidationError(
                "Écris exactement SUPPRIMER DEFINITIVEMENT."
            )
        return value


class EmailTwoFactorConfirmSerializer(serializers.Serializer):
    challenge_token = serializers.CharField(
        max_length=1000,
        write_only=True,
    )
    code = serializers.RegexField(
        regex=r"^\d{6}$",
        write_only=True,
        error_messages={
            "invalid": "Saisis le code à six chiffres reçu par e-mail.",
        },
    )


class EmailTwoFactorSettingsSerializer(CurrentPasswordSerializer):
    enabled = serializers.BooleanField()
