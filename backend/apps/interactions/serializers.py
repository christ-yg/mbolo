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



class ReceivedLikeSerializer(serializers.Serializer):
    """
    Représentation volontairement masquée d’un like reçu.

    La version gratuite n’expose jamais :

    - l’identifiant du profil auteur ;
    - son nom public ;
    - son e-mail ;
    - sa biographie ;
    - l’URL de sa photo.

    L’identifiant retourné correspond uniquement à l’interaction
    reçue. Il permet de répondre via un endpoint serveur contrôlé.
    """

    interaction_id = serializers.UUIDField(
        source="id",
        read_only=True,
    )

    city = serializers.SerializerMethodField()
    age_range = serializers.SerializerMethodField()
    dating_intent = serializers.SerializerMethodField()
    has_photo = serializers.SerializerMethodField()

    received_at = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    is_identity_revealed = serializers.SerializerMethodField()

    def get_city(self, interaction) -> str:
        return (
            interaction.actor.profile.get_city_display()
            or "Ville non précisée"
        )

    def get_age_range(self, interaction) -> str:
        age = interaction.actor.profile.age

        if age is None:
            return "Âge non précisé"

        lower_bound = (age // 5) * 5
        lower_bound = max(18, lower_bound)
        upper_bound = lower_bound + 4

        return f"{lower_bound}–{upper_bound} ans"

    def get_dating_intent(self, interaction) -> str:
        return (
            interaction.actor.profile.get_dating_intent_display()
            or "Intention non précisée"
        )

    def get_has_photo(self, interaction) -> bool:
        return bool(
            interaction.actor.profile.photos.exists()
        )

    def get_is_identity_revealed(self, interaction) -> bool:
        # Préparation explicite pour une future entitlement premium.
        return False


class ReceivedLikeResponseSerializer(serializers.Serializer):
    """
    Valide la réponse apportée à un like reçu.
    """

    decision = serializers.ChoiceField(
        choices=InteractionDecision.choices,
        required=True,
    )


class ReceivedLikeActionResultSerializer(serializers.Serializer):
    """
    Réponse après acceptation ou refus d’un like masqué.
    """

    decision = serializers.ChoiceField(
        choices=InteractionDecision.choices,
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

    revealed_profile = DiscoveryProfileSerializer(
        read_only=True,
        allow_null=True,
    )



class UnmatchResponseSerializer(serializers.Serializer):
    """
    Réponse publique après suppression logique d'un match.

    Les messages ne sont pas supprimés : seule l'accessibilité
    de la relation est désactivée.
    """

    match_id = serializers.UUIDField(read_only=True)
    conversation_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
    )
    deactivated = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
