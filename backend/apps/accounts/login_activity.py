from rest_framework.request import Request

from apps.core.security_logging import (
    get_client_ip,
    pseudonymize_identifier,
)

from .models import LoginActivity, User


def _device_label(request: Request) -> str:
    """Déduit une description générale sans conserver le User-Agent complet."""
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
    fingerprint = pseudonymize_identifier(get_client_ip(request)) or ""
    activity = LoginActivity.objects.create(
        user=user,
        method=method,
        device=_device_label(request),
        ip_fingerprint=fingerprint[:12],
    )
    retained_ids = list(
        LoginActivity.objects.filter(user=user)
        .values_list("id", flat=True)[:50]
    )
    LoginActivity.objects.filter(user=user).exclude(
        id__in=retained_ids,
    ).delete()
    return activity
