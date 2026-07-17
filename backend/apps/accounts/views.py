from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event

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

    La route est publique, mais exige un jeton CSRF,
    car elle modifie les données de l'application.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def post(
        self,
        request: Request,
    ) -> Response:
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

        log_security_event(
            request=request,
            event="auth.register",
            outcome="success",
            reason="account_created",
            user=user,
            email=user.email,
        )

        return Response(
            {
                "data": {
                    "id": str(user.id),
                    "email": user.email,
                    "isEmailVerified": (
                        user.is_email_verified
                    ),
                },
                "message": (
                    "Compte créé. La vérification "
                    "de l'adresse e-mail sera nécessaire."
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

    Les événements sont journalisés sans stocker
    les identifiants en clair.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    throttle_classes = (
        LoginIPThrottle,
        LoginEmailThrottle,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        """
        Vérifie les identifiants puis ouvre une session.
        """

        serializer = LoginSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        submitted_email = request.data.get(
            "email",
            "",
        )

        if not isinstance(
            submitted_email,
            str,
        ):
            submitted_email = ""

        try:
            serializer.is_valid(
                raise_exception=True,
            )
        except ValidationError:
            log_security_event(
                request=request,
                event="auth.login",
                outcome="failure",
                reason=getattr(
                    serializer,
                    "failure_reason",
                    "invalid_credentials",
                ),
                email=submitted_email,
            )

            raise

        user = serializer.validated_data[
            "user"
        ]

        # Django renouvelle automatiquement l'identifiant
        # de session afin de limiter les attaques
        # par fixation de session.
        login(
            request,
            user,
        )

        log_security_event(
            request=request,
            event="auth.login",
            outcome="success",
            reason="authenticated",
            user=user,
            email=user.email,
        )

        return Response(
            {
                "data": {
                    "id": str(user.id),
                    "email": user.email,
                    "isEmailVerified": (
                        user.is_email_verified
                    ),
                },
                "message": "Connexion réussie.",
            },
            status=status.HTTP_200_OK,
        )

    def throttled(
        self,
        request: Request,
        wait: float,
    ) -> None:
        """
        Journalise les requêtes de connexion bloquées
        par la limitation Redis.

        DRF générera ensuite automatiquement la réponse HTTP 429.
        """

        submitted_email = request.data.get(
            "email",
            "",
        )

        if not isinstance(
            submitted_email,
            str,
        ):
            submitted_email = ""

        log_security_event(
            request=request,
            event="auth.login",
            outcome="blocked",
            reason="rate_limited",
            email=submitted_email,
        )

        return super().throttled(
            request,
            wait,
        )


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class LogoutView(APIView):
    """
    Déconnecte l'utilisateur et détruit la session active.
    """

    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        """
        Journalise la déconnexion puis détruit la session.

        La journalisation est effectuée avant logout(),
        car request.user deviendra ensuite anonyme.
        """

        current_user = request.user

        log_security_event(
            request=request,
            event="auth.logout",
            outcome="success",
            reason="session_destroyed",
            user=current_user,
            email=getattr(
                current_user,
                "email",
                None,
            ),
        )

        logout(
            request,
        )

        return Response(
            {
                "message": "Déconnexion réussie.",
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(RetrieveAPIView):
    """
    Retourne les informations minimales
    de l'utilisateur connecté.
    """

    serializer_class = (
        CurrentUserSerializer
    )

    permission_classes = (
        IsAuthenticated,
    )

    def get_object(
        self,
    ) -> User:
        """
        Retourne uniquement l'utilisateur
        associé à la requête.
        """

        request: Request = self.request

        return request.user
