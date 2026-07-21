"""
Serializers de la messagerie privée Mbolo.
"""

from rest_framework import serializers

from apps.accounts.presence import get_user_presence
from apps.profiles.serializers import (
    DiscoveryProfileSerializer,
)

from .models import Conversation, Message


class ConversationCreateSerializer(
    serializers.Serializer
):
    """
    Données acceptées pour ouvrir une conversation.
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
    is_read = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = Message

        fields = (
            "id",
            "body",
            "created_at",
            "read_at",
            "is_read",
            "is_mine",
        )

        read_only_fields = fields

    def get_is_mine(
        self,
        message: Message,
    ) -> bool:
        request = self.context["request"]

        return message.sender_id == request.user.id


class ConversationSerializer(
    serializers.ModelSerializer
):
    """
    Représentation sécurisée d'une conversation.
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

    unread_count = (
        serializers.SerializerMethodField()
    )

    other_presence = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Conversation

        fields = (
            "id",
            "match_id",
            "other_profile",
            "last_message",
            "unread_count",
            "other_presence",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_other_profile(
        self,
        conversation: Conversation,
    ) -> dict:
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

    def get_unread_count(
        self,
        conversation: Conversation,
    ) -> int:
        request = self.context["request"]

        return conversation.unread_count_for_user(
            request.user
        )

    def get_other_presence(
        self,
        conversation: Conversation,
    ) -> dict[str, object]:
        request = self.context["request"]
        profile = conversation.other_profile_for_user(
            request.user
        )
        return get_user_presence(profile.user)


class MarkConversationReadSerializer(
    serializers.Serializer
):
    """
    Réponse retournée après le marquage comme lu.
    """

    conversation_id = serializers.UUIDField(
        read_only=True,
    )

    marked_count = serializers.IntegerField(
        read_only=True,
    )

    read_at = serializers.DateTimeField(
        read_only=True,
    )


class UnreadCountSerializer(
    serializers.Serializer
):
    """
    Nombre total de messages non lus.
    """

    unread_count = serializers.IntegerField(
        read_only=True,
    )


class TypingStatusInputSerializer(serializers.Serializer):
    """État de saisie transmis par le participant connecté."""

    is_typing = serializers.BooleanField(required=True)


class TypingStatusSerializer(serializers.Serializer):
    """Réponse après mise à jour de l'état de saisie."""

    conversation_id = serializers.UUIDField(read_only=True)
    is_typing = serializers.BooleanField(read_only=True)
    expires_in_seconds = serializers.IntegerField(read_only=True)


class OtherTypingStatusSerializer(serializers.Serializer):
    """État public de saisie de l'autre participant."""

    conversation_id = serializers.UUIDField(read_only=True)
    other_is_typing = serializers.BooleanField(read_only=True)
