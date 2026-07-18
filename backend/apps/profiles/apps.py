from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """
    Configuration de l'application des profils de rencontre.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
    verbose_name = "Profils de rencontre"
