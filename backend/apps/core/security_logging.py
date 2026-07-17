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

# Les noms d'événements et les raisons doivent rester simples.
# Cette expression interdit notamment les retours à la ligne,
# afin de limiter les risques d'injection dans les journaux.
SAFE_LABEL_PATTERN = re.compile(
    r"^[a-z0-9_.-]{1,64}$"
)


security_logger = logging.getLogger(
    SECURITY_LOGGER_NAME,
)

# Configuration locale autonome.
#
# Plus tard, en production, ce logger sera envoyé vers :
# - CloudWatch ;
# - un SIEM ;
# - OpenSearch ;
# - Grafana Loki ;
# - ou une autre plateforme centralisée.
#
# Nous évitons d'ajouter plusieurs handlers si Django recharge
# automatiquement le module pendant le développement.
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

# Empêche l'événement d'être affiché une deuxième fois
# par le logger racine de Python ou Django.
security_logger.propagate = False


def _sanitize_label(
    value: str | None,
    default: str,
) -> str:
    """
    Valide un libellé destiné aux journaux.

    Les valeurs doivent contenir uniquement :
    - lettres minuscules ;
    - chiffres ;
    - points ;
    - tirets ;
    - underscores.

    Cette validation évite qu'une valeur contrôlée par un client
    puisse injecter des caractères spéciaux dans les journaux.
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

    Les retours chariot et sauts de ligne sont supprimés afin
    de conserver un événement sur une seule ligne.
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

    Exemples de données concernées :
    - adresse e-mail ;
    - adresse IP.

    Le HMAC utilise la clé secrète Django. La valeur originale
    n'est jamais écrite dans le journal.

    La pseudonymisation reste déterministe :
    la même valeur produira le même hachage dans cet environnement,
    ce qui permet de corréler plusieurs événements de sécurité.
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
    Récupère l'adresse IP utilisée pour la journalisation locale.

    Nous utilisons uniquement REMOTE_ADDR.

    Nous ne faisons pas encore confiance à X-Forwarded-For,
    car cet en-tête peut être falsifié lorsqu'aucun reverse proxy
    de confiance n'est chargé de le remplacer.

    La valeur retournée sera ensuite pseudonymisée.
    """

    client_ip = request.META.get(
        "REMOTE_ADDR",
        "",
    )

    if not isinstance(client_ip, str):
        return ""

    return client_ip.strip()


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

    Paramètres :
    - request : requête HTTP concernée ;
    - event : catégorie d'événement ;
    - outcome : résultat, par exemple success ou failure ;
    - reason : raison technique contrôlée ;
    - user : utilisateur Django si disponible ;
    - email : e-mail utilisé, pseudonymisé avant journalisation.

    Aucune donnée d'authentification sensible n'est acceptée.
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

    # separators réduit les espaces inutiles et produit
    # un événement JSON compact adapté à l'ingestion SIEM.
    serialized_payload = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

    security_logger.info(
        serialized_payload
    )
