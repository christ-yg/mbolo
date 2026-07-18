"""
Configuration Django du module de gestion des photos.

Cette application est volontairement séparée de l'application
profiles afin de distinguer :

- les informations textuelles du profil ;
- les fichiers multimédias ;
- les règles de stockage ;
- le traitement sécurisé des images ;
- les futures tâches de modération visuelle.
"""

from django.apps import AppConfig


class PhotosConfig(AppConfig):
    """
    Configuration du module Photos.
    """

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.photos"

    verbose_name = "Photos des profils"

    def ready(self) -> None:
        """
        Charge les signaux liés à la suppression des fichiers.

        L'import est effectué ici afin que Django enregistre
        les receivers une seule fois au démarrage.
        """

        from . import signals  # noqa: F401
