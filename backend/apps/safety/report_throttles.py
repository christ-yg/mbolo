"""
Limitation anti-abus des signalements utilisateurs.

La limitation repose sur le cache Django actuellement connecté
à Redis dans l'environnement de développement Mbolo.

Principe :

    un utilisateur authentifié
    peut créer au maximum 5 signalements
    pendant une période de 24 heures.

Cette limitation ne remplace pas :

- l'analyse des signalements ;
- la détection comportementale ;
- la modération humaine ;
- la journalisation ;
- les contrôles administratifs.

Elle constitue une première barrière contre le spam.
"""

from typing import Final

from django.conf import settings
from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle


class ReportCreateThrottle(BaseThrottle):
    """
    Limite les créations de signalements par utilisateur.

    Le compteur est rattaché à l'identifiant interne du compte,
    et non à l'adresse e-mail.

    Cela évite de stocker une donnée personnelle lisible
    dans les clés Redis.
    """

    # Nom de l'espace Redis utilisé par cette fonctionnalité.
    cache_prefix: Final[str] = "safety-report-create"

    # Une journée exprimée en secondes.
    default_window_seconds: Final[int] = 24 * 60 * 60

    def __init__(self) -> None:
        """
        Charge la limite depuis les paramètres Django.

        Une valeur par défaut de 5 est utilisée tant qu'aucune
        configuration spécifique n'est déclarée.
        """

        self.limit = int(
            getattr(
                settings,
                "SAFETY_REPORTS_PER_DAY",
                5,
            )
        )

        self.window_seconds = int(
            getattr(
                settings,
                "SAFETY_REPORT_WINDOW_SECONDS",
                self.default_window_seconds,
            )
        )

        self.current_count = 0

    def get_cache_key(
        self,
        request: Request,
    ) -> str | None:
        """
        Construit la clé Redis du compteur.

        Les utilisateurs anonymes sont gérés par IsAuthenticated.
        Aucun compteur utilisateur n'est donc créé pour eux.
        """

        user = request.user

        if not user.is_authenticated:
            return None

        return (
            f"{self.cache_prefix}:"
            f"user:{user.pk}"
        )

    def allow_request(
        self,
        request: Request,
        view,
    ) -> bool:
        """
        Autorise ou refuse la création du signalement.

        Étapes :

        1. créer le compteur s'il n'existe pas ;
        2. incrémenter le compteur s'il existe ;
        3. refuser lorsque la limite est dépassée.

        cache.add() est utilisé avant cache.incr() afin d'éviter
        une erreur lorsque la clé n'existe pas encore.
        """

        cache_key = self.get_cache_key(
            request
        )

        if cache_key is None:
            # La permission IsAuthenticated décidera du refus.
            return True

        # Première tentative :
        #
        # cache.add retourne True uniquement lorsque la clé
        # n'existait pas encore.
        created = cache.add(
            cache_key,
            1,
            timeout=self.window_seconds,
        )

        if created:
            self.current_count = 1
            return True

        try:
            self.current_count = cache.incr(
                cache_key
            )
        except ValueError:
            # Défense contre une expiration de clé survenue
            # entre cache.add() et cache.incr().
            cache.set(
                cache_key,
                1,
                timeout=self.window_seconds,
            )

            self.current_count = 1

        return self.current_count <= self.limit

    def wait(self) -> int:
        """
        Indique au client le délai maximal avant une nouvelle tentative.

        Cette valeur peut être utilisée dans l'en-tête Retry-After
        de la réponse HTTP 429.
        """

        return self.window_seconds
