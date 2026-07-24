from rest_framework import serializers

from apps.profiles.models import Profile
from apps.profiles.serializers import (
    DiscoveryProfileSerializer,
)
from apps.subscriptions.services import get_subscription_state

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


class RewindStateSerializer(serializers.Serializer):
    """
    État minimal du Rewind, sans exposer l'historique privé.
    """

    entitled = serializers.BooleanField(read_only=True)
    available = serializers.BooleanField(read_only=True)
    reason = serializers.CharField(read_only=True)


class RewindResponseSerializer(serializers.Serializer):
    """
    Résultat du retour arrière : le profil restauré est public uniquement.
    """

    rewound = serializers.BooleanField(read_only=True)
    profile = DiscoveryProfileSerializer(read_only=True)


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
    profile_id = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

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
        return self._can_reveal_identity()

    def _can_reveal_identity(self) -> bool:
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            return False

        state = get_subscription_state(request.user)
        return bool(state["entitlements"]["see_likers"])

    def get_profile_id(self, interaction):
        if not self._can_reveal_identity():
            return None
        return interaction.actor.profile.id

    def get_display_name(self, interaction):
        if not self._can_reveal_identity():
            return None
        return interaction.actor.profile.display_name

    def get_image_url(self, interaction):
        if not self._can_reveal_identity():
            return None

        photo = interaction.actor.profile.photos.order_by(
            "position", "created_at"
        ).first()

        if photo is None or not photo.image:
            return None

        request = self.context.get("request")
        url = photo.image.url
        return request.build_absolute_uri(url) if request else url


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
