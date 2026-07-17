from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration de l'application chargée de l'identité
    et du cycle de vie des comptes Mbolo.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Comptes utilisateurs"
