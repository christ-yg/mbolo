from datetime import date
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from rest_framework import serializers

from apps.photos.serializers import ProfilePhotoSerializer
from apps.subscriptions.services import get_subscription_state

from .models import (
    DatingIntent,
    GabonCity,
    Gender,
    Interest,
    Profile,
    ProfileVerification,
    SearchPreferences,
)
from .locations import public_distance_label


class ProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur privé du profil de l'utilisateur connecté.

    Il est utilisé sur :

        GET   /api/v1/profiles/me/
        PATCH /api/v1/profiles/me/

    Il ne doit pas être utilisé directement pour afficher
    les profils des autres utilisateurs.
    """

    age = serializers.IntegerField(
        read_only=True,
    )

    gender_label = serializers.CharField(
        source="get_gender_display",
        read_only=True,
    )

    city_label = serializers.CharField(
        source="get_city_display",
        read_only=True,
    )

    dating_intent_label = serializers.CharField(
        source="get_dating_intent_display",
        read_only=True,
    )

    is_complete = serializers.BooleanField(
        read_only=True,
    )

    interests = serializers.ListField(
        child=serializers.ChoiceField(
            choices=Interest.choices,
        ),
        allow_empty=True,
        max_length=8,
        required=False,
    )

    class Meta:
        model = Profile

        fields = (
            "id",
            "display_name",
            "birth_date",
            "age",
            "gender",
            "gender_label",
            "city",
            "city_label",
            "biography",
            "dating_intent",
            "dating_intent_label",
            "interests",
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
        Normalise le nom public.

        Exemple :

            "   Christ     YG   "

        devient :

            "Christ YG"
        """

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
        """
        Supprime les espaces inutiles placés
        avant et après la biographie.
        """

        return value.strip()

    def validate_interests(
        self,
        value: list[str],
    ) -> list[str]:
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Un centre d'intérêt ne peut être sélectionné qu'une fois."
            )

        return value

    def validate_birth_date(
        self,
        value: date,
    ) -> date:
        """
        Exécute les validateurs du champ birth_date.

        Ces validateurs contrôlent notamment :

        - l'interdiction des dates futures ;
        - l'âge minimum de 18 ans.
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
        Vérifie l'état final du profil lors d'un PATCH.

        Lors d'un PATCH, certains champs ne sont pas envoyés.
        Nous combinons donc :

        - les nouvelles valeurs ;
        - les anciennes valeurs du profil.
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


class ProfileVerificationSerializer(serializers.ModelSerializer):
    """
    État privé de la vérification du profil connecté.

    Le selfie, son chemin de stockage et les informations administratives
    internes ne sont volontairement jamais renvoyés au navigateur.
    """

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    can_submit = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = ProfileVerification
        fields = (
            "status",
            "status_label",
            "can_submit",
            "is_verified",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_can_submit(
        self,
        verification: ProfileVerification,
    ) -> bool:
        return verification.status in {
            ProfileVerification.Status.NOT_SUBMITTED,
            ProfileVerification.Status.REJECTED,
        }

    def get_is_verified(
        self,
        verification: ProfileVerification,
    ) -> bool:
        return (
            verification.status
            == ProfileVerification.Status.APPROVED
        )


class SearchPreferencesSerializer(
    serializers.ModelSerializer
):
    """
    Sérialiseur privé des préférences de découverte.
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

    advanced_filters_available = serializers.SerializerMethodField()
    advanced_filters_effective = serializers.SerializerMethodField()

    ADVANCED_FIELDS = (
        "preferred_cities",
        "preferred_dating_intents",
        "maximum_distance_km",
        "only_verified_profiles",
        "only_profiles_with_photos",
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
            "only_profiles_with_photos",
            "advanced_filters_available",
            "advanced_filters_effective",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "advanced_filters_available",
            "advanced_filters_effective",
            "created_at",
            "updated_at",
        )

    def _advanced_filters_available(self) -> bool:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return bool(
            get_subscription_state(request.user)["entitlements"][
                "advanced_filters"
            ]
        )

    def get_advanced_filters_available(self, _instance) -> bool:
        return self._advanced_filters_available()

    def get_advanced_filters_effective(self, _instance) -> bool:
        return self._advanced_filters_available()

    @staticmethod
    def validate_unique_list(
        value: list[str],
    ) -> list[str]:
        """
        Refuse les valeurs dupliquées.

        Exemple refusé :

            ["libreville", "libreville"]
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
        Vérifie que l'âge maximum reste supérieur
        ou égal à l'âge minimum.
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

        if not self._advanced_filters_available():
            changed_advanced_fields = []

            for field_name in self.ADVANCED_FIELDS:
                if field_name not in attrs:
                    continue

                current_value = (
                    getattr(instance, field_name)
                    if instance is not None
                    else self.fields[field_name].get_default()
                )

                if attrs[field_name] != current_value:
                    changed_advanced_fields.append(field_name)

            if changed_advanced_fields:
                raise serializers.ValidationError(
                    {
                        field_name: (
                            "Ce filtre avancé nécessite un abonnement "
                            "Mbolo Plus ou Prestige actif."
                        )
                        for field_name in changed_advanced_fields
                    }
                )

        return attrs


class DiscoveryProfileSerializer(
    serializers.ModelSerializer
):
    """
    Sérialiseur public et limité des profils de découverte.

    Principe de minimisation des données :

    nous n'exposons que les informations nécessaires
    pour permettre à un utilisateur d'évaluer un profil.

    Données volontairement absentes :

    - adresse e-mail ;
    - numéro de téléphone ;
    - date de naissance exacte ;
    - identifiant du compte User ;
    - préférences privées ;
    - informations administratives.
    """

    age = serializers.IntegerField(
        read_only=True,
    )

    is_verified = serializers.SerializerMethodField()
    interest_labels = serializers.SerializerMethodField()
    common_interests = serializers.SerializerMethodField()
    common_interest_labels = serializers.SerializerMethodField()
    compatibility_score = serializers.SerializerMethodField()
    distance_label = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Profile

        fields = (
            "id",
            "display_name",
            "age",
            "gender",
            "city",
            "biography",
            "dating_intent",
            "is_verified",
            "photos",
            "interests",
            "interest_labels",
            "common_interests",
            "common_interest_labels",
            "compatibility_score",
            "distance_label",
        )

        read_only_fields = fields

    def get_distance_label(self, profile: Profile) -> str | None:
        """
        Expose uniquement une tranche arrondie, jamais des coordonnées.
        """

        return public_distance_label(
            getattr(profile, "distance_km", None)
        )

    def get_photos(self, profile: Profile):
        photos = profile.photos.filter(
            moderation_status="approved",
        ).order_by("position", "created_at")
        return ProfilePhotoSerializer(
            photos, many=True, context=self.context
        ).data

    def get_is_verified(
        self,
        profile: Profile,
    ) -> bool:
        """
        Indique qu'une demande de vérification humaine a été approuvée.
        """

        return profile.is_identity_verified

    def get_interest_labels(self, profile: Profile) -> list[str]:
        labels = dict(Interest.choices)
        return [
            labels[value]
            for value in profile.interests
            if value in labels
        ]

    def get_common_interests(self, profile: Profile) -> list[str]:
        request = self.context.get("request")
        current_profile = getattr(
            getattr(request, "user", None),
            "profile",
            None,
        )

        if current_profile is None:
            return []

        current_values = set(current_profile.interests)
        return [
            value
            for value in profile.interests
            if value in current_values
        ]

    def get_common_interest_labels(
        self,
        profile: Profile,
    ) -> list[str]:
        labels = dict(Interest.choices)
        return [
            labels[value]
            for value in self.get_common_interests(profile)
            if value in labels
        ]

    def get_compatibility_score(self, profile: Profile) -> int:
        request = self.context.get("request")
        current_profile = getattr(
            getattr(request, "user", None),
            "profile",
            None,
        )

        if current_profile is None:
            return 0

        first = set(current_profile.interests)
        second = set(profile.interests)
        union = first | second

        if not union:
            return 0

        return round(
            len(first & second) / len(union) * 100
        )



class PublicProfileDetailSerializer(serializers.ModelSerializer):
    """
    Détail public et minimisé d'un profil autorisé.

    Le backend fournit aussi des libellés humains afin que React
    n'affiche jamais les valeurs techniques comme ``friendship``
    ou ``non_binary``.

    Ce sérialiseur n'expose jamais :
    - l'adresse e-mail ;
    - la date de naissance exacte ;
    - l'identifiant User ;
    - les préférences de recherche ;
    - les données administratives.
    """

    age = serializers.IntegerField(read_only=True)
    is_verified = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    relationship = serializers.SerializerMethodField()

    gender_label = serializers.CharField(
        source="get_gender_display",
        read_only=True,
    )

    city_label = serializers.CharField(
        source="get_city_display",
        read_only=True,
    )

    dating_intent_label = serializers.CharField(
        source="get_dating_intent_display",
        read_only=True,
    )

    current_decision = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "id",
            "display_name",
            "age",
            "gender",
            "gender_label",
            "city",
            "city_label",
            "biography",
            "dating_intent",
            "dating_intent_label",
            "is_verified",
            "photos",
            "relationship",
            "current_decision",
        )
        read_only_fields = fields

    def get_is_verified(self, profile: Profile) -> bool:
        return profile.is_identity_verified

    def get_photos(self, profile: Profile):
        photos = profile.photos.filter(
            moderation_status="approved",
        ).order_by("position", "created_at")
        return ProfilePhotoSerializer(
            photos, many=True, context=self.context
        ).data

    def get_relationship(self, profile: Profile) -> str:
        """
        Indique pourquoi l'accès est autorisé sans révéler
        d'informations privées supplémentaires.
        """

        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            return "public"

        from apps.interactions.models import Match

        current_profile_id = getattr(
            getattr(request.user, "profile", None),
            "id",
            None,
        )

        if current_profile_id is None:
            return "public"

        is_match = Match.objects.filter(
            is_active=True,
        ).filter(
            models.Q(
                profile_one_id=current_profile_id,
                profile_two_id=profile.id,
            )
            | models.Q(
                profile_one_id=profile.id,
                profile_two_id=current_profile_id,
            )
        ).exists()

        return "match" if is_match else "discovery"

    def get_current_decision(
        self,
        profile: Profile,
    ) -> str | None:
        """
        Retourne uniquement la décision du compte connecté vers
        ce profil. Aucune interaction d'un autre membre n'est exposée.
        """

        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            return None

        from apps.interactions.models import Interaction

        return (
            Interaction.objects
            .filter(
                actor=request.user,
                target_profile=profile,
            )
            .values_list("decision", flat=True)
            .first()
        )
