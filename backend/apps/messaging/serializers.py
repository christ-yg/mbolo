"""
Serializers de la messagerie privée Mbolo.
"""

from rest_framework import serializers

from apps.accounts.presence import get_user_presence
from apps.profiles.serializers import (
    DiscoveryProfileSerializer,
)
from apps.subscriptions.services import get_subscription_state

from .models import Conversation, Message, MessageReaction


class MessageReactionInputSerializer(serializers.Serializer):
    emoji = serializers.ChoiceField(
        choices=MessageReaction.ALLOWED_EMOJIS,
        required=False,
        allow_blank=True,
        default="",
    )


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
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=Message.MAX_BODY_LENGTH,
        default="",
    )
    image = serializers.ImageField(required=False, allow_null=True, write_only=True)
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get("body", "").strip() and not attrs.get("image"):
            raise serializers.ValidationError("Ajoutez un texte ou une image.")
        return attrs


class MessageEditSerializer(serializers.Serializer):
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
    read_receipts_available = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()
    reply_preview = serializers.SerializerMethodField()

    class Meta:
        model = Message

        fields = (
            "id",
            "body",
            "image_url",
            "reactions",
            "my_reaction",
            "reply_preview",
            "is_deleted",
            "is_edited",
            "created_at",
            "read_at",
            "is_read",
            "read_receipts_available",
            "is_mine",
        )

        read_only_fields = fields

    is_deleted = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()

    def get_is_deleted(self, message: Message) -> bool:
        return message.deleted_at is not None

    def get_is_edited(self, message: Message) -> bool:
        return message.edited_at is not None

    def get_image_url(self, message: Message) -> str | None:
        if not message.image:
            return None
        request = self.context.get("request")
        url = message.image.url
        return request.build_absolute_uri(url) if request else url

    def get_reactions(self, message: Message) -> list[dict[str, object]]:
        counts: dict[str, int] = {}
        for emoji in message.reactions.values_list("emoji", flat=True):
            counts[emoji] = counts.get(emoji, 0) + 1
        return [{"emoji": emoji, "count": count} for emoji, count in counts.items()]

    def get_my_reaction(self, message: Message) -> str | None:
        request = self.context["request"]
        return (
            message.reactions.filter(user=request.user)
            .values_list("emoji", flat=True)
            .first()
        )

    def get_reply_preview(self, message: Message) -> dict[str, object] | None:
        reply = message.reply_to
        if reply is None:
            return None
        request = self.context["request"]
        if reply.sender_id == request.user.id:
            sender_name = "Vous"
        else:
            sender_name = reply.sender.profile.display_name
        return {
            "id": str(reply.id),
            "body": "" if reply.deleted_at else reply.body[:160],
            "has_image": bool(reply.image) if reply.deleted_at is None else False,
            "sender_name": sender_name,
            "is_deleted": reply.deleted_at is not None,
        }

    def get_is_mine(
        self,
        message: Message,
    ) -> bool:
        request = self.context["request"]

        return message.sender_id == request.user.id

    def get_read_receipts_available(
        self,
        message: Message,
    ) -> bool:
        """
        L'accusé de lecture n'est utile que pour l'auteur du message.
        Sa disponibilité vient de l'abonnement serveur du compte courant.
        """

        request = self.context["request"]

        if message.sender_id != request.user.id:
            return False

        state = get_subscription_state(request.user)
        return bool(state["entitlements"]["read_receipts"])

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # La base conserve read_at pour le compteur de messages non lus,
        # mais un compte gratuit ne reçoit jamais cette information.
        if data["is_mine"] and not data["read_receipts_available"]:
            data["read_at"] = None
            data["is_read"] = False

        return data


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
