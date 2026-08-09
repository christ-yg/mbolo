from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    """Fournit au frontend un jeton et le cookie CSRF correspondant."""

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        return Response(
            {"csrfToken": get_token(request)},
            status=status.HTTP_200_OK,
        )


def _database_is_ready() -> bool:
    """Vérifie PostgreSQL sans exposer de détail technique au client."""

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError:
        return False

    return True


def _cache_is_ready() -> bool:
    """Vérifie Redis avec une écriture temporaire et une lecture immédiate."""

    cache_key = "health:readiness"
    cache_value = "ok"

    try:
        cache.set(cache_key, cache_value, timeout=10)
        return cache.get(cache_key) == cache_value
    except Exception:
        # Le détail est volontairement masqué dans la réponse publique.
        return False


class LivenessCheckView(APIView):
    """Confirme uniquement que le processus Django répond aux requêtes."""

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        return Response(
            {"status": "ok"},
            status=status.HTTP_200_OK,
        )


class ReadinessCheckView(APIView):
    """Confirme que Django, PostgreSQL et Redis sont réellement disponibles."""

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        if not _database_is_ready() or not _cache_is_ready():
            return Response(
                {"status": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"status": "ok"},
            status=status.HTTP_200_OK,
        )


# Compatibilité avec l'ancien import et l'ancienne route /api/v1/health/.
HealthCheckView = ReadinessCheckView
