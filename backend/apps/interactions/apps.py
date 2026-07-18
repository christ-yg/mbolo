from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    """
    Configuration Django du module des interactions.

    Cette application gère :

    - les likes ;
    - les passes ;
    - la détection des likes réciproques ;
    - la création des matchs ;
    - la consultation des matchs de l'utilisateur connecté.
    """

    # Type de clé primaire utilisé par défaut pour les modèles
    # qui ne déclarent pas explicitement leur propre identifiant.
    default_auto_field = "django.db.models.BigAutoField"

    # Chemin Python complet de l'application.
    name = "apps.interactions"

    # Nom lisible affiché dans l'administration Django.
    verbose_name = "Interactions et matchs"
