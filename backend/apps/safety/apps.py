from django.apps import AppConfig


class SafetyConfig(AppConfig):
    """
    Configuration Django du module de sécurité communautaire.

    Ce module prendra progressivement en charge :

    - les blocages entre utilisateurs ;
    - les signalements ;
    - les mesures de modération ;
    - la protection contre le harcèlement ;
    - l'exclusion des utilisateurs bloqués de la découverte ;
    - l'interdiction d'interactions entre comptes bloqués.
    """

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.safety"

    verbose_name = "Sécurité communautaire"
