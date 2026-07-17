from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    CurrentUserSerializer,
    LoginSerializer,
    RegistrationSerializer,
)
from .throttles import (
    LoginEmailThrottle,
    LoginIPThrottle,
)


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class RegisterView(APIView):
    """
    Crée un nouveau compte Mbolo.

    Cette route est publique, mais elle exige un jeton CSRF,
    car elle modifie les données de l'application.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """
        Valide les données reçues puis crée le compte.
        """

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
    Authentifie un utilisateur et crée une session Django.

    Les tentatives sont limitées :
    - par adresse IP ;
    - par adresse e-mail.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    throttle_classes = (
        LoginIPThrottle,
        LoginEmailThrottle,
    )

    def post(self, request: Request) -> Response:
        """
        Vérifie les identifiants puis ouvre une session.
        """

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
    Déconnecte l'utilisateur et détruit la session active.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        """
        Supprime la session serveur de l'utilisateur.
        """

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
    """

    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> User:
        """
        Retourne uniquement l'utilisateur associé à la requête.
        """

        request: Request = self.request

        return request.user
