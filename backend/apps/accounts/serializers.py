from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .email_verification import (
    ExpiredEmailVerificationToken,
    InvalidEmailVerificationToken,
    read_email_verification_token,
)
from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    """Données minimales de l'utilisateur connecté."""

    class Meta:
        model = User

        fields = (
            "id",
            "email",
            "is_email_verified",
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

        try:
            return User.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
                is_email_verified=False,
                is_phone_verified=False,
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
