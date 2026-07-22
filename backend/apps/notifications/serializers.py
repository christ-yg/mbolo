
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Représentation publique d'une notification.

    recipient, source_key et metadata ne sont pas exposés :
    ils sont réservés à la logique interne du serveur.
    """

    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "title",
            "body",
            "target_path",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields


class NotificationUnreadCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField(read_only=True)


class MarkAllNotificationsReadSerializer(serializers.Serializer):
    marked_count = serializers.IntegerField(read_only=True)
    read_at = serializers.DateTimeField(read_only=True)
