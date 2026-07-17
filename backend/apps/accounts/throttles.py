import hashlib
import hmac
import time
from typing import Final

from django.conf import settings
from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle


class AtomicRedisThrottle(BaseThrottle):
    """
    Limiteur générique utilisant Redis.

    Les compteurs sont partagés entre les processus Django
    et les identifiants sont pseudonymisés avant stockage.
    """

    cache_prefix: Final[str] = "auth-throttle"
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

        current_window = (
            int(time.time()) // self.window_seconds
        )

        return (
            f"{self.cache_prefix}:"
            f"{self.__class__.__name__}:"
            f"{digest}:"
            f"{current_window}"
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
    """
    Limite les tentatives provenant d'une même adresse IP.
    """

    limit = 10
    window_seconds = 60

    def get_identifier(
        self,
        request: Request,
        view,
    ) -> str:
        return str(
            request.META.get(
                "REMOTE_ADDR",
                "",
            )
        )


class LoginEmailThrottle(AtomicRedisThrottle):
    """
    Limite les tentatives visant une même adresse e-mail.
    """

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
