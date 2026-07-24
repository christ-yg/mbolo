"""
Historique minimal et alertes de connexion du compte Mbolo.

Ce module ne conserve jamais l'adresse IP exacte ni le User-Agent complet.
Il dérive seulement :

- un libellé général de l'appareil ;
- une empreinte réseau pseudonymisée et courte ;
- la méthode d'authentification ;
- la date de connexion.

Lorsqu'un compte possède déjà un historique et qu'une nouvelle combinaison
appareil/empreinte apparaît, une alerte de sécurité est créée. La première
connexion sert de référence et ne déclenche donc pas d'alerte.
"""

import logging

from rest_framework.request import Request

from apps.core.security_logging import (
    get_client_ip,
    pseudonymize_identifier,
)

from .models import LoginActivity, User


logger = logging.getLogger(__name__)


def _device_label(request: Request) -> str:
    """
    Déduit une description générale sans conserver le User-Agent complet.

    Le User-Agent brut est utilisé uniquement en mémoire pendant la requête,
    puis abandonné. Seul un libellé court comme « Chrome · Windows » est
    enregistré.
    """

    agent = str(request.META.get("HTTP_USER_AGENT", "")).lower()

    if "android" in agent:
        system = "Android"
    elif "iphone" in agent or "ipad" in agent:
        system = "iPhone/iPad"
    elif "windows" in agent:
        system = "Windows"
    elif "macintosh" in agent or "mac os" in agent:
        system = "macOS"
    elif "linux" in agent:
        system = "Linux"
    else:
        system = "Appareil inconnu"

    if "edg/" in agent:
        browser = "Edge"
    elif "yabrowser" in agent:
        browser = "Yandex Browser"
    elif "firefox/" in agent:
        browser = "Firefox"
    elif "chrome/" in agent:
        browser = "Chrome"
    elif "safari/" in agent:
        browser = "Safari"
    else:
        browser = ""

    return f"{browser} · {system}".strip(" ·")[:120]


def record_login_activity(
    *,
    request: Request,
    user: User,
    method: str,
) -> LoginActivity:
    """
    Enregistre une connexion puis déclenche éventuellement une alerte.

    Une connexion est considérée comme reconnue lorsqu'une activité précédente
    du même compte possède à la fois :

    - le même libellé général d'appareil ;
    - la même empreinte réseau pseudonymisée.

    La première connexion du compte est une référence initiale et ne déclenche
    pas d'alerte. Une erreur d'alerte ne doit jamais empêcher une connexion
    légitime : elle est donc journalisée côté serveur, sans donnée sensible.
    """

    device = _device_label(request)
    fingerprint = pseudonymize_identifier(get_client_ip(request)) or ""
    fingerprint = fingerprint[:12]

    previous_activities = LoginActivity.objects.filter(user=user)
    has_previous_activity = previous_activities.exists()

    is_recognized_connection = previous_activities.filter(
        device=device,
        ip_fingerprint=fingerprint,
    ).exists()

    activity = LoginActivity.objects.create(
        user=user,
        method=method,
        device=device,
        ip_fingerprint=fingerprint,
    )

    if has_previous_activity and not is_recognized_connection:
        try:
            # Import local pour éviter une dépendance circulaire au chargement
            # des modules Django.
            from .login_alerts import notify_unrecognized_login

            notify_unrecognized_login(
                user=user,
                activity=activity,
            )
        except Exception:
            # Aucune adresse IP, aucun e-mail et aucun User-Agent ne sont
            # ajoutés au log. La connexion reste valide même si l'alerte échoue.
            logger.exception(
                "Impossible de créer l'alerte de nouvelle connexion."
            )

    retained_ids = list(
        LoginActivity.objects.filter(user=user)
        .values_list("id", flat=True)[:50]
    )

    LoginActivity.objects.filter(user=user).exclude(
        id__in=retained_ids,
    ).delete()

    return activity
