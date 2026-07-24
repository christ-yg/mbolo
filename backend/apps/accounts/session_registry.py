"""
Registre sécurisé des appareils connectés à Mbolo.
"""

import hmac
import hashlib

from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework.request import Request

from .models import AccountSession, User


def hash_session_key(session_key: str) -> str:
    """
    Produit une empreinte HMAC de la clé de session.

    La clé brute reste uniquement dans la table django_session.
    """

    return hmac.new(
        key=settings.SECRET_KEY.encode("utf-8"),
        msg=session_key.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def register_current_session(
    *,
    request: Request,
    user: User,
    device: str,
    ip_fingerprint: str,
) -> AccountSession | None:
    """
    Enregistre ou actualise la session courante après authentification.
    """

    if request.session.session_key is None:
        request.session.save()

    session_key = request.session.session_key

    if not session_key:
        return None

    account_session, _ = AccountSession.objects.update_or_create(
        session_key_hash=hash_session_key(session_key),
        defaults={
            "user": user,
            "device": device[:120],
            "ip_fingerprint": ip_fingerprint[:16],
        },
    )

    # Rétention défensive : 30 appareils maximum par compte.
    retained_ids = list(
        AccountSession.objects.filter(user=user)
        .values_list("id", flat=True)[:30]
    )
    AccountSession.objects.filter(user=user).exclude(
        id__in=retained_ids,
    ).delete()

    return account_session


def remove_stale_account_sessions(*, user: User) -> None:
    """
    Supprime du registre les sessions expirées ou déjà absentes.
    """

    active_hashes = {
        hash_session_key(session.session_key)
        for session in Session.objects.filter(
            expire_date__gte=timezone.now(),
        )
    }

    AccountSession.objects.filter(user=user).exclude(
        session_key_hash__in=active_hashes,
    ).delete()


def revoke_registered_session(
    *,
    user: User,
    account_session: AccountSession,
    current_session_key: str | None,
) -> bool:
    """
    Révoque une session donnée sans exposer sa clé brute.
    """

    if account_session.user_id != user.id:
        return False

    current_hash = (
        hash_session_key(current_session_key)
        if current_session_key
        else None
    )

    if current_hash == account_session.session_key_hash:
        return False

    deleted = False

    for session in Session.objects.filter(
        expire_date__gte=timezone.now(),
    ).iterator():
        if hash_session_key(session.session_key) != (
            account_session.session_key_hash
        ):
            continue

        session.delete()
        deleted = True
        break

    account_session.delete()

    return deleted
