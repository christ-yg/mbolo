"""
Historique minimal, alertes et registre des connexions Mbolo.
"""

import logging

from rest_framework.request import Request

from apps.core.security_logging import (
    get_client_ip,
    pseudonymize_identifier,
)

from .models import LoginActivity, User
from .session_registry import register_current_session


logger = logging.getLogger(__name__)


def _device_label(request: Request) -> str:
    """
    Déduit un libellé général sans conserver le User-Agent complet.
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
    Enregistre la connexion, le registre de session et l'alerte éventuelle.
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

    register_current_session(
        request=request,
        user=user,
        device=device,
        ip_fingerprint=fingerprint,
    )

    if has_previous_activity and not is_recognized_connection:
        try:
            from .login_alerts import notify_unrecognized_login

            notify_unrecognized_login(
                user=user,
                activity=activity,
            )
        except Exception:
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
