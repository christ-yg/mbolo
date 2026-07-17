from django.contrib.auth import login, logout
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
    LoginSerializer,
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


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class LoginView(APIView):
    """
    Authentifie un utilisateur et crée une session Django sécurisée.

    La fonction login() effectue une rotation de la clé de session,
    ce qui limite les attaques par fixation de session.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.validated_data["user"]

        # Django renouvelle l'identifiant de session lors
        # de l'authentification afin d'éviter la réutilisation
        # d'une session anonyme prédéfinie par un attaquant.
        login(
            request,
            user,
        )

        return Response(
            {
                "data": {
                    "id": str(user.id),
                    "email": user.email,
                    "isEmailVerified": user.is_email_verified,
                },
                "message": "Connexion réussie.",
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class LogoutView(APIView):
    """
    Déconnecte l'utilisateur et détruit sa session actuelle.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        logout(request)

        return Response(
            {
                "message": "Déconnexion réussie.",
            },
            status=status.HTTP_200_OK,
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
