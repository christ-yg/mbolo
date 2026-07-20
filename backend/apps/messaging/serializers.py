from rest_framework import serializers

from apps.profiles.serializers import (
    DiscoveryProfileSerializer,
)

from .models import Conversation, Message


class ConversationCreateSerializer(
    serializers.Serializer
):
    """
    Données acceptées pour créer ou récupérer une conversation.

    Le client envoie uniquement l'identifiant du match.
    """

    match_id = serializers.UUIDField(
        required=True,
    )


class MessageCreateSerializer(
    serializers.Serializer
):
    """
    Données acceptées pour envoyer un message.

    Le client n'envoie jamais l'identité de l'expéditeur.
    """

    body = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=Message.MAX_BODY_LENGTH,
    )


class MessageSerializer(
    serializers.ModelSerializer
):
    """
    Représentation publique et sécurisée d'un message.
    """

    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message

        fields = (
            "id",
            "body",
            "created_at",
            "is_mine",
        )

        read_only_fields = fields

    def get_is_mine(
        self,
        message: Message,
    ) -> bool:
        """
        Indique si le message appartient au compte connecté.

        Aucun identifiant User n'est transmis au frontend.
        """

        request = self.context["request"]

        return message.sender_id == request.user.id


class ConversationSerializer(
    serializers.ModelSerializer
):
    """
    Représentation sécurisée d'une conversation.

    Informations exposées :

    - identifiant de conversation ;
    - identifiant du match ;
    - profil public de l'autre participant ;
    - dernier message ;
    - dates de création et de mise à jour.

    Informations non exposées :

    - identifiants User ;
    - adresses e-mail ;
    - numéros de téléphone ;
    - profils internes des deux participants.
    """

    match_id = serializers.UUIDField(
        source="match.id",
        read_only=True,
    )

    other_profile = (
        serializers.SerializerMethodField()
    )

    last_message = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Conversation

        fields = (
            "id",
            "match_id",
            "other_profile",
            "last_message",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_other_profile(
        self,
        conversation: Conversation,
    ) -> dict:
        """
        Retourne uniquement le profil public de l'autre personne.
        """

        request = self.context["request"]

        profile = (
            conversation.other_profile_for_user(
                request.user
            )
        )

        return DiscoveryProfileSerializer(
            profile,
            context=self.context,
        ).data

    def get_last_message(
        self,
        conversation: Conversation,
    ) -> dict | None:
        """
        Retourne le dernier message de la conversation.
        """

        message = (
            conversation.messages
            .order_by("-created_at")
            .first()
        )

        if message is None:
            return None

        return MessageSerializer(
            message,
            context=self.context,
        ).data
