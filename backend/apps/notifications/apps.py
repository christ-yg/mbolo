
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """
    Configuration de l'application de notifications.

    Cette application stocke les événements destinés à un compte :
    messages, futurs matchs, likes et alertes de sécurité.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notifications"
