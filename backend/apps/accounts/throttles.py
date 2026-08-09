import hashlib
import hmac
from typing import Final

from django.conf import settings
from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle

from apps.core.security_logging import get_client_ip


class AtomicRedisThrottle(BaseThrottle):
    """
    Limiteur générique utilisant Redis.

    Les identifiants sont pseudonymisés avant stockage.
    Les compteurs sont partagés entre les processus Django.
    """

    cache_prefix: Final[str] = "security-throttle"
    limit: int
    window_seconds: int

    def __init__(self) -> None:
        self.current_count = 0
        self.retry_after = self.window_seconds

    def get_identifier(
        self,
        request: Request,
        view,
    ) -> str:
        raise NotImplementedError

    def build_cache_key(
        self,
        identifier: str,
    ) -> str:
        digest = hmac.new(
            key=settings.SECRET_KEY.encode("utf-8"),
            msg=identifier.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        return (
            f"{self.cache_prefix}:"
            f"{self.__class__.__name__}:"
            f"{digest}"
        )

    def allow_request(
        self,
        request: Request,
        view,
    ) -> bool:
        identifier = self.get_identifier(
            request,
            view,
        )

        if not identifier:
            return True

        cache_key = self.build_cache_key(
            identifier,
        )

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
                cache_key,
            )
        except ValueError:
            cache.set(
                cache_key,
                1,
                timeout=self.window_seconds,
            )
            self.current_count = 1

        return self.current_count <= self.limit

    def wait(self) -> int:
        return self.retry_after


class LoginIPThrottle(AtomicRedisThrottle):
    """Dix tentatives par minute pour une même IP."""

    limit = 10
    window_seconds = 60

    def get_identifier(
        self,
        request: Request,
        view,
    ) -> str:
        return get_client_ip(request)


class LoginEmailThrottle(AtomicRedisThrottle):
    """Cinq tentatives par minute pour un même e-mail."""

    limit = 5
    window_seconds = 60

    def get_identifier(
        self,
        request: Request,
        view,
    ) -> str:
        email = request.data.get(
            "email",
            "",
        )

        if not isinstance(email, str):
            return ""

        return email.strip().lower()


class EmailVerificationRequestIPThrottle(AtomicRedisThrottle):
    """
    Dix demandes de vérification maximum par cinq minutes
    depuis une même adresse IP.
    """

    limit = 10
    window_seconds = 300

    def get_identifier(
        self,
        request: Request,
        view,
    ) -> str:
        return get_client_ip(request)


class EmailVerificationRequestEmailThrottle(AtomicRedisThrottle):
    """
    Trois demandes maximum par quinze minutes
    pour une même adresse e-mail.
    """

    limit = 3
    window_seconds = 900

    def get_identifier(
        self,
        request: Request,
        view,
    ) -> str:
        email = request.data.get(
            "email",
            "",
        )

        if not isinstance(email, str):
            return ""

        return email.strip().lower()


class PasswordResetRequestIPThrottle(EmailVerificationRequestIPThrottle):
    """Dix demandes par cinq minutes pour une IP."""


class PasswordResetRequestEmailThrottle(EmailVerificationRequestEmailThrottle):
    """Trois demandes par quinze minutes pour une adresse."""


class PasswordResetConfirmIPThrottle(AtomicRedisThrottle):
    """Dix validations de lien par cinq minutes pour une IP."""

    limit = 10
    window_seconds = 300

    def get_identifier(self, request: Request, view) -> str:
        return get_client_ip(request)


class RegistrationIPThrottle(AtomicRedisThrottle):
    """Dix créations de compte maximum par heure pour une IP."""

    limit = 10
    window_seconds = 3600

    def get_identifier(self, request: Request, view) -> str:
        return get_client_ip(request)


class EmailTwoFactorConfirmIPThrottle(AtomicRedisThrottle):
    """Vingt validations 2FA par cinq minutes pour une IP."""

    limit = 20
    window_seconds = 300

    def get_identifier(self, request: Request, view) -> str:
        return get_client_ip(request)


class EmailTwoFactorChallengeThrottle(AtomicRedisThrottle):
    """Cinq essais par cinq minutes pour un même challenge signé."""

    limit = 5
    window_seconds = 300

    def get_identifier(self, request: Request, view) -> str:
        token = request.data.get("challenge_token", "")

        if not isinstance(token, str):
            return ""

        return token.strip()
