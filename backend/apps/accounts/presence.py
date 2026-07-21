"""
Gestion légère de la présence utilisateur Mbolo.

La présence instantanée est stockée dans le cache Django (Redis en local)
afin d'éviter une écriture SQL à chaque battement du frontend.
"""

from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone


ONLINE_WINDOW_SECONDS = 120
PRESENCE_CACHE_TIMEOUT_SECONDS = 60 * 60 * 24 * 30


def _presence_cache_key(user_id: object) -> str:
    return f"mbolo:presence:{user_id}"


def touch_user_presence(user) -> dict[str, object]:
    """Enregistre une activité récente et considère l'utilisateur en ligne."""
    now = timezone.now()
    payload = {
        "last_seen_at": now.isoformat(),
        "forced_offline": False,
    }
    cache.set(
        _presence_cache_key(user.id),
        payload,
        timeout=PRESENCE_CACHE_TIMEOUT_SECONDS,
    )
    return {
        "is_online": True,
        "last_seen_at": now,
    }


def mark_user_offline(user) -> dict[str, object]:
    """Marque explicitement la session comme hors ligne lors de la déconnexion."""
    now = timezone.now()
    payload = {
        "last_seen_at": now.isoformat(),
        "forced_offline": True,
    }
    cache.set(
        _presence_cache_key(user.id),
        payload,
        timeout=PRESENCE_CACHE_TIMEOUT_SECONDS,
    )
    return {
        "is_online": False,
        "last_seen_at": now,
    }


def get_user_presence(user) -> dict[str, object]:
    """Retourne une présence publique minimale et calculée côté serveur."""
    cached_payload = cache.get(
        _presence_cache_key(user.id),
    )

    last_seen_at = None
    forced_offline = False

    if isinstance(cached_payload, dict):
        raw_last_seen_at = cached_payload.get("last_seen_at")
        forced_offline = bool(
            cached_payload.get("forced_offline", False)
        )

        if isinstance(raw_last_seen_at, str):
            try:
                last_seen_at = timezone.datetime.fromisoformat(
                    raw_last_seen_at
                )
            except ValueError:
                last_seen_at = None

    if last_seen_at is None:
        last_seen_at = user.last_login

    is_online = False
    if last_seen_at is not None and not forced_offline:
        is_online = (
            timezone.now() - last_seen_at
            <= timedelta(seconds=ONLINE_WINDOW_SECONDS)
        )

    return {
        "is_online": is_online,
        "last_seen_at": last_seen_at,
    }
