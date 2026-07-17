from django.db import connection
from django.db.utils import OperationalError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


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
