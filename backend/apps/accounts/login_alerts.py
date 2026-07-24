"""
Alertes de nouvelle connexion pour Mbolo.

Ce module crée trois canaux complémentaires :

1. une notification durable dans le centre de notifications ;
2. une diffusion privée en temps réel par WebSocket ;
3. un e-mail de sécurité, lorsque le membre conserve ce canal actif.

Principes de sécurité :

- aucune adresse IP exacte ;
- aucun User-Agent complet ;
- aucun cookie ni jeton ;
- aucune donnée de session ;
- notification interne toujours active ;
- création idempotente grâce à l'identifiant de l'activité ;
- échec d'e-mail non bloquant ;
- destination interne fixe vers la page de sécurité.
"""

import logging
from datetime import timezone as datetime_timezone

from django.conf import settings
from django.core.mail import send_mail

from apps.notifications.models import Notification
from apps.notifications.services import broadcast_notification_created

from .models import LoginActivity, User


logger = logging.getLogger(__name__)


def _format_login_date_utc(activity: LoginActivity) -> str:
    """
    Formate explicitement la date en UTC pour les e-mails.
    """

    utc_created_at = activity.created_at.astimezone(datetime_timezone.utc)

    return utc_created_at.strftime("%d/%m/%Y à %H:%M UTC")


def _send_new_login_email(
    *,
    user: User,
    activity: LoginActivity,
) -> None:
    """
    Envoie l'e-mail d'alerte sans exposer de donnée sensible.
    """

    subject = "Nouvelle connexion détectée sur votre compte Mbolo"

    message = (
        "Bonjour,\n\n"
        "Une nouvelle connexion à votre compte Mbolo a été détectée.\n\n"
        f"Appareil : {activity.device or 'Appareil inconnu'}\n"
        f"Date : {_format_login_date_utc(activity)}\n"
        f"Méthode : "
        f"{'Code e-mail confirmé' if activity.method == 'email_2fa' else 'Mot de passe'}\n\n"
        "Si cette connexion vient de vous, aucune action n'est nécessaire.\n"
        "Dans le cas contraire, changez immédiatement votre mot de passe "
        "et déconnectez les autres appareils depuis la page Sécurité.\n\n"
        "Mbolo ne conserve pas votre adresse IP exacte dans cet historique."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def notify_unrecognized_login(
    *,
    user: User,
    activity: LoginActivity,
) -> Notification:
    """
    Crée et diffuse une alerte idempotente pour une activité inhabituelle.

    Le canal interne est obligatoire. Le choix du membre ne concerne que
    l'e-mail complémentaire.
    """

    notification, created = Notification.objects.get_or_create(
        recipient=user,
        source_key=f"security-login:{activity.id}",
        defaults={
            "kind": Notification.Kind.SECURITY,
            "title": "Nouvelle connexion détectée",
            "body": (
                f"Connexion depuis {activity.device or 'un appareil inconnu'}. "
                "Vérifie ton compte si ce n’était pas toi."
            ),
            "target_path": "/security",
            "metadata": {
                "login_activity_id": str(activity.id),
                "device": activity.device,
                "method": activity.method,
            },
        },
    )

    if created:
        broadcast_notification_created(
            notification=notification,
            event_name="security.notification",
            extra_payload={
                "security_event": "unrecognized_login",
            },
        )

        if user.login_alert_emails_enabled:
            try:
                _send_new_login_email(
                    user=user,
                    activity=activity,
                )
            except Exception:
                logger.exception(
                    "Impossible d'envoyer l'e-mail d'alerte de connexion."
                )

    return notification
