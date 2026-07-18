from datetime import date
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    DatingIntent,
    GabonCity,
    Gender,
    Profile,
    SearchPreferences,
)


class ProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur du profil de l'utilisateur connecté.
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
        normalized_value = " ".join(
            value.split()
        )

        if (
            normalized_value
            and len(normalized_value) < 2
        ):
            raise serializers.ValidationError(
                "Le nom public doit contenir "
                "au moins deux caractères."
            )

        return normalized_value

    def validate_biography(
        self,
        value: str,
    ) -> str:
        return value.strip()

    def validate_birth_date(
        self,
        value: date,
    ) -> date:
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

        if (
            future_is_discoverable
            and not all(future_values.values())
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


class SearchPreferencesSerializer(
    serializers.ModelSerializer
):
    """
    Sérialiseur privé des préférences de découverte.

    Le client ne peut jamais remplacer :
    - l'identifiant ;
    - le propriétaire ;
    - les dates techniques.
    """

    preferred_genders = serializers.ListField(
        child=serializers.ChoiceField(
            choices=Gender.choices,
        ),
        allow_empty=True,
        required=False,
    )

    preferred_cities = serializers.ListField(
        child=serializers.ChoiceField(
            choices=GabonCity.choices,
        ),
        allow_empty=True,
        required=False,
    )

    preferred_dating_intents = serializers.ListField(
        child=serializers.ChoiceField(
            choices=DatingIntent.choices,
        ),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = SearchPreferences

        fields = (
            "id",
            "minimum_age",
            "maximum_age",
            "preferred_genders",
            "preferred_cities",
            "preferred_dating_intents",
            "maximum_distance_km",
            "only_verified_profiles",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    @staticmethod
    def validate_unique_list(
        value: list[str],
    ) -> list[str]:
        """
        Refuse les doublons tout en conservant l'ordre.
        """

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "La liste ne doit pas contenir de doublons."
            )

        return value

    def validate_preferred_genders(
        self,
        value: list[str],
    ) -> list[str]:
        return self.validate_unique_list(
            value
        )

    def validate_preferred_cities(
        self,
        value: list[str],
    ) -> list[str]:
        return self.validate_unique_list(
            value
        )

    def validate_preferred_dating_intents(
        self,
        value: list[str],
    ) -> list[str]:
        return self.validate_unique_list(
            value
        )

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Vérifie la cohérence de la tranche d'âge finale.

        Cette logique fonctionne également lors d'un PATCH
        ne contenant qu'un seul des deux âges.
        """

        instance = self.instance

        current_minimum = (
            instance.minimum_age
            if instance is not None
            else 18
        )

        current_maximum = (
            instance.maximum_age
            if instance is not None
            else 45
        )

        future_minimum = attrs.get(
            "minimum_age",
            current_minimum,
        )

        future_maximum = attrs.get(
            "maximum_age",
            current_maximum,
        )

        if future_minimum > future_maximum:
            raise serializers.ValidationError(
                {
                    "maximum_age": (
                        "L'âge maximum doit être supérieur "
                        "ou égal à l'âge minimum."
                    )
                }
            )

        return attrs
