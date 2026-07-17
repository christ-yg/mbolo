from django.db import connection
from django.db.utils import OperationalError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie


@method_decorator(
    ensure_csrf_cookie,
    name="dispatch",
)
class CSRFTokenView(APIView):
    """
    Fournit un jeton CSRF au frontend.

    Le navigateur reçoit également le cookie CSRF correspondant.

    Ce jeton devra être envoyé dans l'en-tête HTTP X-CSRFToken
    pour toutes les opérations qui modifient des données.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        """
        Génère ou récupère le jeton CSRF de la session courante.
        """

        csrf_token = get_token(request)

        return Response(
            {
                "csrfToken": csrf_token,
            },
            status=status.HTTP_200_OK,
        )



class HealthCheckView(APIView):
    """
    Endpoint public de contrôle de santé.

    L'endpoint vérifie uniquement si l'application peut joindre
    sa base de données.

    Il ne retourne volontairement aucune information technique
    détaillée afin de limiter la fuite d'informations.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        """
        Retourne un état minimal de disponibilité.

        Réponse réussie :
        {
            "status": "ok"
        }

        Réponse dégradée :
        {
            "status": "unavailable"
        }
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            return Response(
                {"status": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"status": "ok"},
            status=status.HTTP_200_OK,
        )
