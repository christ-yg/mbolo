"""Client serveur E-Billing pour les paiements Mobile Money Mbolo.

Les secrets restent exclusivement dans l'environnement du backend Django.
Le client utilise OAuth2 client_credentials, crée une facture E-Billing,
déclenche le push USSD puis permet de revalider le statut auprès du
prestataire. Aucun PIN Mobile Money ne transite par Mbolo.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


class EbillingError(RuntimeError):
    """Erreur contrôlée lors d'un échange avec E-Billing."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class EbillingCheckout:
    bill_id: str
    ussd_push_id: str


_token_lock = threading.Lock()
_cached_token: str | None = None
_cached_token_expires_at = 0.0


def normalize_gabon_msisdn(value: str) -> str:
    """Normalise un numéro gabonais vers 241XXXXXXXXX, sans + ni espaces."""

    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if digits.startswith("00241"):
        digits = digits[2:]
    if digits.startswith("241"):
        normalized = digits
    elif digits.startswith("0"):
        normalized = "241" + digits[1:]
    else:
        normalized = "241" + digits

    if len(normalized) < 11 or len(normalized) > 12:
        raise ValueError(
            "Numéro Mobile Money invalide. Utilise un numéro gabonais, "
            "par exemple 077xxxxxx ou 24177xxxxxxx."
        )
    return normalized


class EbillingClient:
    def __init__(self) -> None:
        self.base_url = str(settings.EBILLING_BASE_URL).rstrip("/")
        self.client_id = str(settings.EBILLING_CLIENT_ID)
        self.client_secret = str(settings.EBILLING_CLIENT_SECRET)
        self.timeout = int(settings.EBILLING_HTTP_TIMEOUT_SECONDS)

        if not self.base_url or not self.client_id or not self.client_secret:
            raise EbillingError(
                "E-Billing n'est pas complètement configuré côté serveur."
            )

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict | None = None,
        form: dict | None = None,
        authenticated: bool = True,
    ) -> dict:
        headers = {"Accept": "application/json"}
        body = None

        if form is not None:
            body = urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if authenticated:
            headers["Authorization"] = f"Bearer {self.get_access_token()}"

        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method.upper(),
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                detail = {"message": raw}
            message = (
                detail.get("message")
                or detail.get("error_description")
                or detail.get("error")
                or f"E-Billing a répondu HTTP {exc.code}."
            )
            raise EbillingError(str(message), status_code=exc.code) from exc
        except (URLError, TimeoutError) as exc:
            raise EbillingError(
                "E-Billing est temporairement inaccessible."
            ) from exc
        except json.JSONDecodeError as exc:
            raise EbillingError("Réponse E-Billing non JSON.") from exc

    def get_access_token(self) -> str:
        global _cached_token, _cached_token_expires_at

        if _cached_token and _cached_token_expires_at > time.time() + 60:
            return _cached_token

        with _token_lock:
            if _cached_token and _cached_token_expires_at > time.time() + 60:
                return _cached_token
            payload = self._request(
                "POST",
                "/oauth/token",
                form={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                authenticated=False,
            )
            token = payload.get("access_token")
            if not token:
                raise EbillingError(
                    "Authentification E-Billing invalide: access_token manquant."
                )
            expires_in = int(payload.get("expires_in") or 3300)
            _cached_token = str(token)
            _cached_token_expires_at = time.time() + expires_in
            return _cached_token

    def create_invoice(
        self,
        *,
        amount_xaf: int,
        payer_phone: str,
        payer_name: str,
        description: str,
        external_reference: str,
    ) -> str:
        payload = self._request(
            "POST",
            "/api/v1/merchant/e_bills",
            data={
                "amount": amount_xaf,
                "payer_msisdn": payer_phone,
                "payer_name": payer_name,
                "short_description": description,
                "external_reference": external_reference,
                "client_transaction_id": external_reference,
                "email": False,
                "sms": False,
                "expiry_period": 24,
            },
        )
        bill_id = payload.get("bill_id") or payload.get("e_bill", {}).get("bill_id")
        if not bill_id:
            raise EbillingError("Réponse E-Billing invalide: bill_id manquant.")
        return str(bill_id)

    def trigger_ussd_push(
        self,
        *,
        bill_id: str,
        operator: str,
        payer_phone: str,
    ) -> str:
        payload = self._request(
            "POST",
            f"/api/v2/merchant/e_bills/{bill_id}/ussd_push",
            data={
                "payment_system_name": operator,
                "payer_msisdn": payer_phone,
            },
        )
        push = payload.get("ussd_push") or {}
        push_id = push.get("id")
        if not push_id:
            raise EbillingError(
                "Réponse E-Billing invalide: ussd_push.id manquant."
            )
        return str(push_id)

    def initiate_mobile_money(
        self,
        *,
        amount_xaf: int,
        payer_phone: str,
        payer_name: str,
        operator: str,
        description: str,
        external_reference: str,
    ) -> EbillingCheckout:
        phone = normalize_gabon_msisdn(payer_phone)
        bill_id = self.create_invoice(
            amount_xaf=amount_xaf,
            payer_phone=phone,
            payer_name=payer_name,
            description=description,
            external_reference=external_reference,
        )
        ussd_push_id = self.trigger_ussd_push(
            bill_id=bill_id,
            operator=operator,
            payer_phone=phone,
        )
        return EbillingCheckout(
            bill_id=bill_id,
            ussd_push_id=ussd_push_id,
        )

    def get_ussd_push_status(self, ussd_push_id: str) -> dict:
        return self._request(
            "GET",
            f"/api/v2/merchant/ussd_push/{ussd_push_id}",
        )
