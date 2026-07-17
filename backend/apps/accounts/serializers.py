from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur minimal de l'utilisateur connecté.

    Les champs sensibles ou internes ne sont jamais exposés :
    - mot de passe ;
    - permissions internes ;
    - statut de superutilisateur ;
    - numéro de téléphone ;
    - jetons ;
    - groupes administratifs.
    """

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
    """
    Valide et crée un nouveau compte utilisateur.

    Le mot de passe n'est jamais retourné dans la réponse.
    """

    email = serializers.EmailField(
        max_length=254,
        write_only=True,
    )

    password = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={
            "input_type": "password",
        },
    )

    password_confirmation = serializers.CharField(
        min_length=12,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={
            "input_type": "password",
        },
    )

    def validate_email(self, value: str) -> str:
        """
        Normalise systématiquement l'adresse e-mail.

        Exemple :
        Christ@Example.COM devient christ@example.com.
        """

        normalized_email = (
            User.objects.normalize_email(value)
            .strip()
            .lower()
        )

        return normalized_email

    def validate(self, attrs: dict) -> dict:
        """
        Vérifie la confirmation et applique les validateurs
        de mots de passe configurés par Django.
        """

        password = attrs["password"]
        password_confirmation = attrs["password_confirmation"]

        if password != password_confirmation:
            raise serializers.ValidationError(
                {
                    "password_confirmation": (
                        "Les deux mots de passe ne correspondent pas."
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
                {
                    "password": list(exc.messages),
                }
            ) from exc

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> User:
        """
        Crée le compte dans une transaction atomique.

        Si une erreur se produit, aucune création partielle
        ne doit rester dans la base de données.
        """

        validated_data.pop(
            "password_confirmation",
        )

        email = validated_data["email"]
        password = validated_data["password"]

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                is_email_verified=False,
                is_phone_verified=False,
            )
        except IntegrityError as exc:
            # Message volontairement générique afin de limiter
            # l'énumération des comptes existants.
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Impossible de créer le compte avec "
                        "les informations fournies."
                    )
                }
            ) from exc

        return user



class LoginSerializer(serializers.Serializer):
    """
    Valide les identifiants de connexion.

    Le message d'erreur reste volontairement générique afin
    de ne pas révéler si une adresse e-mail existe.
    """

    email = serializers.EmailField(
        max_length=254,
        write_only=True,
    )

    password = serializers.CharField(
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={
            "input_type": "password",
        },
    )

    def validate(self, attrs: dict) -> dict:
        """
        Normalise l'e-mail puis authentifie l'utilisateur.
        """

        request = self.context.get("request")

        email = (
            User.objects.normalize_email(attrs["email"])
            .strip()
            .lower()
        )

        password = attrs["password"]

        user = authenticate(
            request=request,
            email=email,
            password=password,
        )

        # Message identique pour :
        # - compte inexistant ;
        # - mot de passe incorrect ;
        # - compte non authentifiable.
        if user is None:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Adresse e-mail ou mot de passe incorrect."
                    )
                }
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Ce compte ne peut pas être utilisé."
                    )
                }
            )

        if user.is_suspended:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Ce compte ne peut pas être utilisé."
                    )
                }
            )

        attrs["user"] = user

        return attrs
