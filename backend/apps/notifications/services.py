
"""
Services métier du centre de notifications.

Toutes les créations et modifications passent par cette couche afin
de garder les règles de déduplication et de sécurité au même endroit.
"""

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import Notification


@dataclass(frozen=True)
class NotificationCreationResult:
    notification: Notification
    created: bool


def get_unread_notification_count(*, actor) -> int:
    if not getattr(actor, "is_authenticated", False):
        return 0

    return Notification.objects.filter(
        recipient=actor,
        read_at__isnull=True,
    ).count()


@transaction.atomic
def create_message_notification(
    *,
    recipient,
    sender_display_name: str,
    conversation_id,
    message_id,
    body_preview: str,
) -> NotificationCreationResult:
    """
    Crée une notification durable et idempotente pour un message.

    source_key empêche la création de plusieurs lignes si la diffusion
    temps réel est rejouée ou si une requête est répétée.
    """

    normalized_sender = (
        sender_display_name or "Un membre"
    ).strip()[:80]

    normalized_preview = (
        body_preview or ""
    ).strip()[:160]

    notification, created = Notification.objects.get_or_create(
        recipient=recipient,
        source_key=f"message:{message_id}",
        defaults={
            "kind": Notification.Kind.MESSAGE,
            "title": f"{normalized_sender} t’a envoyé un message",
            "body": normalized_preview,
            "target_path": f"/messages/{conversation_id}",
            "metadata": {
                "conversation_id": str(conversation_id),
                "message_id": str(message_id),
            },
        },
    )

    return NotificationCreationResult(
        notification=notification,
        created=created,
    )


@transaction.atomic
def mark_notification_as_read(*, actor, notification_id):
    notification = (
        Notification.objects
        .select_for_update()
        .filter(
            id=notification_id,
            recipient=actor,
        )
        .first()
    )

    if notification is None:
        return None

    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=("read_at",))

    return notification


@transaction.atomic
def mark_all_notifications_as_read(*, actor) -> tuple[int, object]:
    read_at = timezone.now()

    marked_count = (
        Notification.objects
        .filter(
            recipient=actor,
            read_at__isnull=True,
        )
        .update(read_at=read_at)
    )

    return marked_count, read_at


@transaction.atomic
def delete_notification(*, actor, notification_id) -> bool:
    deleted_count, _ = (
        Notification.objects
        .filter(
            id=notification_id,
            recipient=actor,
        )
        .delete()
    )

    return deleted_count > 0
