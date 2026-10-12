
from rest_framework import serializers

from .models import Notification, NotificationPreference


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


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    security_enabled = serializers.SerializerMethodField()
    quiet_start = serializers.TimeField(
        format="%H:%M",
        input_formats=("%H:%M",),
    )
    quiet_end = serializers.TimeField(
        format="%H:%M",
        input_formats=("%H:%M",),
    )

    class Meta:
        model = NotificationPreference
        fields = (
            "notifications_enabled",
            "messages_enabled",
            "matches_enabled",
            "likes_enabled",
            "security_enabled",
            "quiet_hours_enabled",
            "quiet_start",
            "quiet_end",
            "timezone_offset_minutes",
            "updated_at",
        )
        read_only_fields = ("security_enabled", "updated_at")

    def get_security_enabled(self, obj) -> bool:
        return True

    def validate(self, attrs):
        start = attrs.get("quiet_start", getattr(self.instance, "quiet_start", None))
        end = attrs.get("quiet_end", getattr(self.instance, "quiet_end", None))
        if start == end:
            raise serializers.ValidationError(
                "Le début et la fin des heures silencieuses doivent différer."
            )
        return attrs
