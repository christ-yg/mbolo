from rest_framework import serializers

from apps.profiles.models import Profile
from apps.profiles.serializers import (
    DiscoveryProfileSerializer,
)

from .models import (
    InteractionDecision,
    Match,
)


class InteractionCreateSerializer(serializers.Serializer):
    """
    Valide une nouvelle interaction.

    Le client envoie uniquement :

        target_profile_id
        decision

    Il ne peut pas envoyer :

        actor
        user_id
        match_id
        created_at

    L'acteur est toujours déterminé par request.user.
    """

    target_profile_id = serializers.UUIDField(
        required=True,
    )

    decision = serializers.ChoiceField(
        choices=InteractionDecision.choices,
        required=True,
    )


class InteractionResponseSerializer(serializers.Serializer):
    """
    Structure de la réponse après un like ou un pass.
    """

    interaction_id = serializers.UUIDField(
        read_only=True,
    )

    decision = serializers.ChoiceField(
        choices=InteractionDecision.choices,
        read_only=True,
    )

    interaction_created = serializers.BooleanField(
        read_only=True,
    )

    matched = serializers.BooleanField(
        read_only=True,
    )

    match_created = serializers.BooleanField(
        read_only=True,
    )

    match_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
    )


class MatchSerializer(serializers.ModelSerializer):
    """
    Sérialiseur sécurisé d'un match.

    Seul le profil de l'autre participant est retourné.

    Nous n'exposons pas :

    - profile_one et profile_two directement ;
    - les e-mails ;
    - les identifiants User ;
    - les interactions ayant déclenché le match.
    """

    other_profile = serializers.SerializerMethodField()

    class Meta:
        model = Match

        fields = (
            "id",
            "other_profile",
            "created_at",
        )

        read_only_fields = fields

    def get_other_profile(
        self,
        match: Match,
    ) -> dict:
        """
        Détermine l'autre participant à partir
        du profil de l'utilisateur connecté.
        """

        request = self.context["request"]

        current_profile = request.user.profile

        other_profile: Profile = (
            match.other_profile_for(
                current_profile
            )
        )

        return DiscoveryProfileSerializer(
            other_profile,
            context=self.context,
        ).data
