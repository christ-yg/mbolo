from datetime import date
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur du profil appartenant à l'utilisateur connecté.

    Les champs techniques et la relation User ne peuvent pas
    être modifiés directement par le client.
    """

    age = serializers.IntegerField(
        read_only=True,
    )

    is_complete = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = Profile

        fields = (
            "id",
            "display_name",
            "birth_date",
            "age",
            "gender",
            "city",
            "biography",
            "dating_intent",
            "is_discoverable",
            "is_complete",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "age",
            "is_complete",
            "created_at",
            "updated_at",
        )

    def validate_display_name(
        self,
        value: str,
    ) -> str:
        """
        Nettoie le nom public et refuse les valeurs trop faibles.
        """

        normalized_value = " ".join(
            value.split()
        )

        if normalized_value and len(normalized_value) < 2:
            raise serializers.ValidationError(
                "Le nom public doit contenir au moins deux caractères."
            )

        return normalized_value

    def validate_biography(
        self,
        value: str,
    ) -> str:
        """
        Supprime les espaces inutiles sans transformer le contenu.
        """

        return value.strip()

    def validate_birth_date(
        self,
        value: date,
    ) -> date:
        """
        Exécute explicitement les validateurs du champ modèle.
        """

        field = Profile._meta.get_field(
            "birth_date"
        )

        try:
            field.run_validators(
                value
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                list(exc.messages)
            ) from exc

        return value

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Valide l'état final du profil, y compris pour PATCH.

        Lors d'une mise à jour partielle, nous fusionnons les nouvelles
        valeurs avec celles déjà enregistrées avant d'évaluer les règles.
        """

        instance = self.instance

        if instance is None:
            return attrs

        future_values = {
            "display_name": attrs.get(
                "display_name",
                instance.display_name,
            ),
            "birth_date": attrs.get(
                "birth_date",
                instance.birth_date,
            ),
            "gender": attrs.get(
                "gender",
                instance.gender,
            ),
            "city": attrs.get(
                "city",
                instance.city,
            ),
            "dating_intent": attrs.get(
                "dating_intent",
                instance.dating_intent,
            ),
        }

        future_is_discoverable = attrs.get(
            "is_discoverable",
            instance.is_discoverable,
        )

        future_is_complete = all(
            future_values.values()
        )

        if (
            future_is_discoverable
            and not future_is_complete
        ):
            raise serializers.ValidationError(
                {
                    "is_discoverable": (
                        "Complétez les informations obligatoires "
                        "avant de rendre le profil visible."
                    )
                }
            )

        if (
            future_is_discoverable
            and not instance.user.is_email_verified
        ):
            raise serializers.ValidationError(
                {
                    "is_discoverable": (
                        "Vérifiez votre adresse e-mail avant "
                        "de rendre le profil visible."
                    )
                }
            )

        return attrs
