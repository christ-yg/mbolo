from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """
    Configuration de l'application de messagerie privée Mbolo.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messaging"
    verbose_name = "Messagerie privée"
