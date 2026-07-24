import hashlib
import secrets
import uuid

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import constant_time_compare

from .models import User


CHALLENGE_TTL_SECONDS = 600
MAX_CONFIRMATION_ATTEMPTS = 5
SIGNING_SALT = "mbolo.accounts.email-2fa"


class InvalidTwoFactorChallenge(Exception):
    pass


def _cache_key(nonce: str) -> str:
    return f"mbolo:email-2fa:{nonce}"


def _code_digest(*, nonce: str, code: str) -> str:
    material = f"{nonce}:{code}:{settings.SECRET_KEY}".encode()
    return hashlib.sha256(material).hexdigest()


def mask_email(email: str) -> str:
    local, separator, domain = email.partition("@")
    if not separator:
        return "***"
    visible = local[:2]
    return f"{visible}{'*' * max(3, len(local) - 2)}@{domain}"


def create_email_two_factor_challenge(user: User) -> tuple[str, str]:
    nonce = uuid.uuid4().hex
    code = f"{secrets.randbelow(1_000_000):06d}"
    cache.set(
        _cache_key(nonce),
        {
            "user_id": str(user.pk),
            "code_digest": _code_digest(nonce=nonce, code=code),
            "attempts": 0,
        },
        timeout=CHALLENGE_TTL_SECONDS,
    )
    token = signing.dumps(
        {"user_id": str(user.pk), "nonce": nonce},
        salt=SIGNING_SALT,
        compress=True,
    )
    send_mail(
        subject="Ton code de connexion Mbolo",
        message=(
            f"Ton code de connexion Mbolo est : {code}\n\n"
            "Il expire dans 10 minutes et ne doit être communiqué "
            "à personne. Si tu n'es pas à l'origine de cette "
            "connexion, change ton mot de passe."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return token, mask_email(user.email)


def consume_email_two_factor_challenge(
    *,
    challenge_token: str,
    code: str,
) -> User:
    try:
        signed_data = signing.loads(
            challenge_token,
            salt=SIGNING_SALT,
            max_age=CHALLENGE_TTL_SECONDS,
        )
    except signing.BadSignature as exc:
        raise InvalidTwoFactorChallenge from exc

    nonce = signed_data.get("nonce")
    user_id = signed_data.get("user_id")
    if not isinstance(nonce, str) or not isinstance(user_id, str):
        raise InvalidTwoFactorChallenge

    key = _cache_key(nonce)
    challenge = cache.get(key)
    if not isinstance(challenge, dict):
        raise InvalidTwoFactorChallenge

    attempts = int(challenge.get("attempts", 0)) + 1
    expected_digest = challenge.get("code_digest", "")
    supplied_digest = _code_digest(nonce=nonce, code=code)
    if not constant_time_compare(expected_digest, supplied_digest):
        if attempts >= MAX_CONFIRMATION_ATTEMPTS:
            cache.delete(key)
        else:
            challenge["attempts"] = attempts
            cache.set(key, challenge, timeout=CHALLENGE_TTL_SECONDS)
        raise InvalidTwoFactorChallenge

    cache.delete(key)
    try:
        return User.objects.get(
            pk=user_id,
            is_active=True,
            is_suspended=False,
            email_2fa_enabled=True,
        )
    except User.DoesNotExist as exc:
        raise InvalidTwoFactorChallenge from exc
