"""
Sérialiseurs publics des signalements.

La séparation entre sérialiseur d'entrée et sérialiseur de sortie
permet d'appliquer le principe de minimisation des privilèges :

- seuls les champs nécessaires sont acceptés ;
- seuls les champs nécessaires sont retournés ;
- les informations internes de modération restent privées.
"""

from rest_framework import serializers

from apps.profiles.models import Profile
from apps.profiles.serializers import DiscoveryProfileSerializer

from .models import (
    Report,
    ReportReason,
)


class ReportCreateSerializer(serializers.Serializer):
    """
    Valide les données publiques nécessaires à un signalement.

    Le déclarant n'est jamais fourni par le client :
    il sera obligatoirement récupéré depuis request.user.
    """

    reported_user_id = serializers.UUIDField(
        required=True,
    )

    reason = serializers.ChoiceField(
        choices=ReportReason.choices,
        required=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
        trim_whitespace=True,
        default="",
    )

    def validate_description(
        self,
        value: str,
    ) -> str:
        """
        Normalise la description du signalement.

        Les espaces multiples sont réduits afin de limiter :

        - les entrées artificiellement volumineuses ;
        - les différences inutiles ;
        - certaines techniques simples d'obfuscation.
        """

        normalized_value = " ".join(
            value.split()
        )

        return normalized_value

    def validate(self, attrs):
        """
        Exige une explication lorsque le motif sélectionné est "other".

        Un motif générique sans aucune description ne serait pas
        exploitable par l'équipe de modération.
        """

        reason = attrs["reason"]

        description = attrs.get(
            "description",
            "",
        )

        if (
            reason == ReportReason.OTHER
            and not description
        ):
            raise serializers.ValidationError(
                {
                    "description": (
                        "Une description est obligatoire "
                        "pour le motif 'other'."
                    )
                }
            )

        return attrs


class ReportListSerializer(serializers.ModelSerializer):
    """
    Représentation publique d'un signalement créé par l'utilisateur.

    Champs volontairement absents :

    - reporter ;
    - reviewed_by ;
    - moderator_note ;
    - resolved_at ;
    - données privées de la personne signalée.
    """

    reported_profile = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Report

        fields = (
            "id",
            "reported_profile",
            "reason",
            "description",
            "status",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_reported_profile(
        self,
        report: Report,
    ):
        """
        Retourne uniquement le profil public minimal.

        L'adresse e-mail, le téléphone et la date de naissance exacte
        ne sont jamais exposés.
        """

        try:
            profile = (
                Profile.objects
                .select_related("user")
                .get(
                    user=report.reported_user,
                )
            )
        except Profile.DoesNotExist:
            return None

        return DiscoveryProfileSerializer(
            profile,
            context=self.context,
        ).data
