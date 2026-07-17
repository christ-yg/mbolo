from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration des fonctionnalités transversales de Mbolo.

    Cette application contient notamment :
    - les endpoints techniques minimaux ;
    - les contrôles de santé ;
    - les éléments communs à plusieurs modules.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Fonctionnalités principales"
