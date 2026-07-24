import hashlib
import hmac
import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from django.conf import settings
from rest_framework.request import Request


SECURITY_LOGGER_NAME = "mbolo.security"

SAFE_LABEL_PATTERN = re.compile(
    r"^[a-z0-9_.-]{1,64}$"
)

security_logger = logging.getLogger(
    SECURITY_LOGGER_NAME,
)

if not security_logger.handlers:
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        logging.Formatter(
            "%(message)s"
        )
    )

    security_logger.addHandler(
        console_handler,
    )

security_logger.setLevel(
    logging.INFO,
)

security_logger.propagate = False


# Seuls les événements directement utiles au membre sont recopiés dans
# l'historique visible du compte. Les événements techniques, de découverte,
# de modération ou d'administration restent exclusivement dans les logs SIEM.
USER_VISIBLE_SECURITY_EVENTS = {
    "auth.password_change",
    "auth.sessions_revoke",
    "auth.email_2fa_settings",
    "auth.login_alert_email_preference",
    "auth.account_deactivate",
    "auth.password_reset_confirm",
}


def _sanitize_label(
    value: str | None,
    default: str,
) -> str:
    """
    Valide un libellé destiné aux journaux.
    """

    if not isinstance(value, str):
        return default

    normalized_value = value.strip().lower()

    if not SAFE_LABEL_PATTERN.fullmatch(
        normalized_value
    ):
        return default

    return normalized_value


def _sanitize_path(
    value: str,
) -> str:
    """
    Nettoie le chemin HTTP avant journalisation.
    """

    sanitized_value = (
        value.replace("\r", "")
        .replace("\n", "")
        .strip()
    )

    return sanitized_value[:512]


def pseudonymize_identifier(
    value: str | None,
) -> str | None:
    """
    Transforme une donnée personnelle en pseudonyme HMAC-SHA256.
    """

    if not isinstance(value, str):
        return None

    normalized_value = value.strip().lower()

    if not normalized_value:
        return None

    secret_key = settings.SECRET_KEY.encode(
        "utf-8"
    )

    return hmac.new(
        key=secret_key,
        msg=normalized_value.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def get_client_ip(
    request: Request,
) -> str:
    """
    Récupère REMOTE_ADDR avant pseudonymisation.
    """

    client_ip = request.META.get(
        "REMOTE_ADDR",
        "",
    )

    if not isinstance(client_ip, str):
        return ""

    return client_ip.strip()


def _persist_user_visible_security_event(
    *,
    event: str,
    outcome: str,
    reason: str,
    user: Any | None,
) -> None:
    """
    Copie un événement autorisé dans l'historique du membre.

    L'import local évite une dépendance circulaire au démarrage de Django.
    Une erreur de persistance ne doit jamais bloquer l'action principale.
    """

    if event not in USER_VISIBLE_SECURITY_EVENTS:
        return

    if (
        user is None
        or not getattr(user, "is_authenticated", False)
        or not getattr(user, "pk", None)
    ):
        return

    try:
        from apps.accounts.models import AccountSecurityEvent

        AccountSecurityEvent.objects.create(
            user=user,
            event=event,
            outcome=outcome,
            reason=reason,
        )

        retained_ids = list(
            AccountSecurityEvent.objects.filter(user=user)
            .values_list("id", flat=True)[:100]
        )

        AccountSecurityEvent.objects.filter(user=user).exclude(
            id__in=retained_ids,
        ).delete()
    except Exception:
        # Le logger technique reste fonctionnel même si la base est indisponible.
        security_logger.exception(
            "Impossible de persister l'événement de sécurité utilisateur."
        )


def log_security_event(
    *,
    request: Request,
    event: str,
    outcome: str,
    reason: str = "not_applicable",
    user: Any | None = None,
    email: str | None = None,
) -> None:
    """
    Écrit un événement de sécurité JSON sur une seule ligne.

    Après la journalisation SIEM, certains événements sensibles sont aussi
    enregistrés dans un historique minimal visible par l'utilisateur.
    """

    safe_event = _sanitize_label(
        event,
        default="security.unknown",
    )

    safe_outcome = _sanitize_label(
        outcome,
        default="unknown",
    )

    safe_reason = _sanitize_label(
        reason,
        default="unknown",
    )

    client_ip = get_client_ip(
        request,
    )

    user_id = None

    if (
        user is not None
        and getattr(user, "is_authenticated", False)
    ):
        user_id = str(
            getattr(user, "pk", "")
        ) or None

    payload = {
        "timestamp": datetime.now(
            UTC
        ).isoformat(),
        "event": safe_event,
        "outcome": safe_outcome,
        "reason": safe_reason,
        "method": request.method,
        "path": _sanitize_path(
            request.path
        ),
        "ip_hash": pseudonymize_identifier(
            client_ip
        ),
        "email_hash": pseudonymize_identifier(
            email
        ),
        "user_id": user_id,
    }

    serialized_payload = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

    security_logger.info(
        serialized_payload
    )

    _persist_user_visible_security_event(
        event=safe_event,
        outcome=safe_outcome,
        reason=safe_reason,
        user=user,
    )
