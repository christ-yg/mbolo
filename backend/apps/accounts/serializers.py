from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

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

    Le mot de passe et sa confirmation sont acceptés uniquement
    en écriture et ne sont jamais retournés dans une réponse.
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

    def validate_email(
        self,
        value: str,
    ) -> str:
        """
        Normalise systématiquement l'adresse e-mail.

        Exemple :
        New.User@Example.COM devient new.user@example.com.
        """

        normalized_email = (
            User.objects.normalize_email(value)
            .strip()
            .lower()
        )

        return normalized_email

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Vérifie la confirmation du mot de passe et applique
        les validateurs de sécurité configurés dans Django.
        """

        password = attrs["password"]

        password_confirmation = attrs[
            "password_confirmation"
        ]

        if password != password_confirmation:
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
                {
                    "password": list(
                        exc.messages
                    ),
                }
            ) from exc

        return attrs

    @transaction.atomic
    def create(
        self,
        validated_data: dict[str, Any],
    ) -> User:
        """
        Crée le compte dans une transaction atomique.

        Si une erreur intervient pendant la création,
        aucune donnée partielle ne reste en base.
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
            # Le message reste générique afin de limiter
            # l'énumération des adresses déjà enregistrées.
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Impossible de créer le compte "
                        "avec les informations fournies."
                    )
                }
            ) from exc

        return user


class LoginSerializer(serializers.Serializer):
    """
    Valide les identifiants de connexion.

    Les erreurs retournées au client restent génériques afin
    de ne pas révéler si une adresse e-mail existe.

    L'attribut failure_reason est exclusivement destiné
    à la journalisation interne de sécurité.
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

    # Cette valeur n'est jamais renvoyée dans la réponse API.
    # Elle permet uniquement à la vue de classifier l'événement
    # de journalisation.
    failure_reason = "invalid_credentials"

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalise l'e-mail puis authentifie l'utilisateur.
        """

        request = self.context.get(
            "request"
        )

        email = (
            User.objects.normalize_email(
                attrs["email"]
            )
            .strip()
            .lower()
        )

        password = attrs["password"]

        user = authenticate(
            request=request,
            email=email,
            password=password,
        )

        # Le message HTTP reste identique pour :
        # - adresse inconnue ;
        # - mot de passe incorrect ;
        # - compte désactivé par le backend ;
        # - compte non authentifiable.
        if user is None:
            self.failure_reason = (
                "invalid_credentials"
            )

            raise serializers.ValidationError(
                {
                    "detail": (
                        "Adresse e-mail ou "
                        "mot de passe incorrect."
                    )
                }
            )

        if not user.is_active:
            self.failure_reason = (
                "account_inactive"
            )

            raise serializers.ValidationError(
                {
                    "detail": (
                        "Ce compte ne peut pas "
                        "être utilisé."
                    )
                }
            )

        if user.is_suspended:
            self.failure_reason = (
                "account_suspended"
            )

            raise serializers.ValidationError(
                {
                    "detail": (
                        "Ce compte ne peut pas "
                        "être utilisé."
                    )
                }
            )

        attrs["email"] = email
        attrs["user"] = user

        return attrs
