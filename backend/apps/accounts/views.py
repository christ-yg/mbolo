from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from .models import User
from .serializers import (
    CurrentUserSerializer,
    RegistrationSerializer,
)


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class RegisterView(APIView):
    """
    Crée un nouveau compte Mbolo.

    Cette route est publique, mais une protection CSRF est exigée
    parce qu'elle réalise une écriture dans la base de données.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = RegistrationSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.save()

        return Response(
            {
                "data": {
                    "id": str(user.id),
                    "email": user.email,
                    "isEmailVerified": user.is_email_verified,
                },
                "message": (
                    "Compte créé. La vérification de l'adresse "
                    "e-mail sera nécessaire."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(RetrieveAPIView):
    """
    Retourne les informations minimales de l'utilisateur connecté.

    L'accès exige une session Django authentifiée.
    Un utilisateur ne peut obtenir que ses propres informations.
    """

    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> User:
        """
        Retourne exclusivement l'utilisateur associé à la requête.

        Aucun identifiant utilisateur n'est accepté dans l'URL,
        ce qui réduit le risque d'accès horizontal non autorisé.
        """

        request: Request = self.request

        return request.user
