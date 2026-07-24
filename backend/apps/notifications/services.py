
"""
Services métier du centre de notifications Mbolo.

Ce module centralise :

- la création idempotente des notifications durables ;
- le calcul du compteur non lu ;
- la diffusion privée par WebSocket ;
- le marquage lu/non lu ;
- la suppression limitée au propriétaire.

Les notifications de like restent volontairement anonymes.
L'identité de la personne qui a liké n'est pas exposée.
"""

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.accounts.realtime import broadcast_account_event

from .models import Notification
from .serializers import NotificationSerializer


@dataclass(frozen=True)
class NotificationCreationResult:
    notification: Notification
    created: bool


def get_unread_notification_count(*, actor) -> int:
    """
    Retourne le nombre de notifications non lues d'un compte.
    """

    if not getattr(actor, "is_authenticated", False):
        return 0

    return Notification.objects.filter(
        recipient=actor,
        read_at__isnull=True,
    ).count()


def broadcast_notification_created(
    *,
    notification: Notification,
    event_name: str,
    extra_payload: dict | None = None,
) -> None:
    """
    Diffuse une notification durable vers le compte destinataire.

    Le payload contient uniquement des données publiques déjà
    autorisées par NotificationSerializer.
    """

    payload = {
        "event": event_name,
        "notification_unread_count": (
            get_unread_notification_count(
                actor=notification.recipient,
            )
        ),
        "notification": NotificationSerializer(
            notification
        ).data,
    }

    if extra_payload:
        payload.update(extra_payload)

    broadcast_account_event(
        user_id=notification.recipient_id,
        event=payload,
    )


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
            "title": (
                f"{normalized_sender} t’a envoyé un message"
            ),
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
def create_like_notification(
    *,
    recipient,
    interaction_id,
    is_super_like: bool = False,
) -> NotificationCreationResult:
    """
    Crée une notification de like respectueuse de la confidentialité.

    L'identité de la personne qui a liké n'est pas stockée dans
    le titre ni dans le corps de la notification publique.
    """

    notification, created = Notification.objects.get_or_create(
        recipient=recipient,
        source_key=(
            f"super-like:{interaction_id}"
            if is_super_like
            else f"like:{interaction_id}"
        ),
        defaults={
            "kind": (
                Notification.Kind.SUPER_LIKE
                if is_super_like
                else Notification.Kind.LIKE
            ),
            "title": (
                "Quelqu’un t’a envoyé un Super Like"
                if is_super_like
                else "Quelqu’un a aimé ton profil"
            ),
            "body": (
                (
                    "Ton profil a particulièrement retenu son attention. "
                    "Réponds depuis l’espace Qui m’a liké."
                )
                if is_super_like
                else (
                    "Continue à découvrir des profils. "
                    "Un like réciproque créera un match."
                )
            ),
            "target_path": "/discovery",
            "metadata": {
                "interaction_id": str(interaction_id),
                "is_super_like": is_super_like,
            },
        },
    )

    return NotificationCreationResult(
        notification=notification,
        created=created,
    )


@transaction.atomic
def create_match_notification(
    *,
    recipient,
    other_display_name: str,
    match_id,
) -> NotificationCreationResult:
    """
    Crée une notification de nouveau match.

    L'identité publique peut être affichée ici, car les deux
    utilisateurs ont exprimé un intérêt réciproque.
    """

    normalized_name = (
        other_display_name or "un membre"
    ).strip()[:80]

    notification, created = Notification.objects.get_or_create(
        recipient=recipient,
        source_key=f"match:{match_id}",
        defaults={
            "kind": Notification.Kind.MATCH,
            "title": f"Nouveau match avec {normalized_name}",
            "body": (
                "Vous vous appréciez mutuellement. "
                "Vous pouvez maintenant commencer à discuter."
            ),
            "target_path": "/matches",
            "metadata": {
                "match_id": str(match_id),
            },
        },
    )

    return NotificationCreationResult(
        notification=notification,
        created=created,
    )


@transaction.atomic
def create_report_status_notification(
    *,
    recipient,
    report_id,
    status: str,
) -> NotificationCreationResult:
    """
    Informe l'auteur d'un signalement de son avancement.

    Le contenu est volontairement générique : aucune identité de
    modérateur, note interne ou information sur le compte signalé
    n'est enregistrée dans la notification publique.
    """

    content_by_status = {
        "under_review": (
            "Ton signalement est en cours d’examen",
            "L’équipe Mbolo a pris en charge ton dossier.",
        ),
        "resolved": (
            "Ton signalement a été traité",
            "L’examen de ton dossier est terminé. Merci d’avoir contribué à la sécurité de Mbolo.",
        ),
        "rejected": (
            "Ton signalement a été classé",
            "L’examen de ton dossier est terminé. Aucun détail confidentiel de modération n’est communiqué.",
        ),
    }

    try:
        title, body = content_by_status[status]
    except KeyError as exc:
        raise ValueError(
            "Statut de signalement non notifiable."
        ) from exc

    notification, created = Notification.objects.get_or_create(
        recipient=recipient,
        source_key=f"report:{report_id}:{status}",
        defaults={
            "kind": Notification.Kind.SYSTEM,
            "title": title,
            "body": body,
            "target_path": "/reports",
            "metadata": {
                "report_id": str(report_id),
                "status": status,
            },
        },
    )

    return NotificationCreationResult(
        notification=notification,
        created=created,
    )


@transaction.atomic
def create_moderation_sanction_notification(
    *,
    recipient,
    sanction_id,
    sanction_type: str,
) -> NotificationCreationResult:
    """
    Notifie une mesure de sécurité sans exposer le dossier interne.
    """

    content_by_type = {
        "warning": (
            "Avertissement de sécurité Mbolo",
            "Ton compte a reçu un avertissement. Consulte les règles de sécurité avant de continuer.",
        ),
        "suspension_7_days": (
            "Compte temporairement suspendu",
            "L’accès à ton compte est suspendu pendant 7 jours pour des raisons de sécurité.",
        ),
        "suspension_30_days": (
            "Compte temporairement suspendu",
            "L’accès à ton compte est suspendu pendant 30 jours pour des raisons de sécurité.",
        ),
        "permanent_suspension": (
            "Compte suspendu",
            "L’accès à ton compte a été suspendu sans échéance pour des raisons de sécurité.",
        ),
    }

    try:
        title, body = content_by_type[sanction_type]
    except KeyError as exc:
        raise ValueError("Type de sanction non notifiable.") from exc

    notification, created = Notification.objects.get_or_create(
        recipient=recipient,
        source_key=f"moderation-sanction:{sanction_id}",
        defaults={
            "kind": Notification.Kind.SECURITY,
            "title": title,
            "body": body,
            "target_path": "/security",
            "metadata": {
                "sanction_id": str(sanction_id),
                "sanction_type": sanction_type,
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
def mark_all_notifications_as_read(
    *,
    actor,
) -> tuple[int, object]:
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
def delete_notification(
    *,
    actor,
    notification_id,
) -> bool:
    deleted_count, _ = (
        Notification.objects
        .filter(
            id=notification_id,
            recipient=actor,
        )
        .delete()
    )

    return deleted_count > 0
