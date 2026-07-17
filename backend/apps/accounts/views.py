from django.contrib.auth import login, logout
from django.db import transaction
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

from .email_verification import (
    send_email_verification_message,
)
from .models import User
from .serializers import (
    CurrentUserSerializer,
    EmailVerificationConfirmSerializer,
    EmailVerificationRequestSerializer,
    LoginSerializer,
    RegistrationSerializer,
)
from .throttles import (
    EmailVerificationRequestEmailThrottle,
    EmailVerificationRequestIPThrottle,
    LoginEmailThrottle,
    LoginIPThrottle,
)


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    def post(
        self,
        request: Request,
    ) -> Response:
        serializer = RegistrationSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.save()

        send_email_verification_message(
            user=user,
        )

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
                    "Compte créé. Un message de "
                    "vérification a été envoyé."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
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
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        submitted_email = request.data.get(
            "email",
            "",
        )

        if not isinstance(submitted_email, str):
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

        user = serializer.validated_data["user"]

        login(request, user)

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
        email = request.data.get("email", "")

        if not isinstance(email, str):
            email = ""

        log_security_event(
            request=request,
            event="auth.login",
            outcome="blocked",
            reason="rate_limited",
            email=email,
        )

        return super().throttled(request, wait)


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(
        self,
        request: Request,
    ) -> Response:
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

        logout(request)

        return Response(
            {"message": "Déconnexion réussie."},
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class EmailVerificationRequestView(APIView):
    """
    Demande ou redemande un e-mail de vérification.

    La réponse reste identique que le compte existe ou non.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    throttle_classes = (
        EmailVerificationRequestIPThrottle,
        EmailVerificationRequestEmailThrottle,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        serializer = EmailVerificationRequestSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email=email,
            is_active=True,
            is_suspended=False,
            is_email_verified=False,
        ).first()

        if user is not None:
            send_email_verification_message(
                user=user,
            )

            log_security_event(
                request=request,
                event="auth.email_verification_request",
                outcome="success",
                reason="message_sent",
                user=user,
                email=email,
            )
        else:
            log_security_event(
                request=request,
                event="auth.email_verification_request",
                outcome="accepted",
                reason="generic_response",
                email=email,
            )

        return Response(
            {
                "message": (
                    "Si un compte éligible correspond à cette "
                    "adresse, un message de vérification sera envoyé."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class EmailVerificationConfirmView(APIView):
    """
    Confirme l'adresse e-mail à partir d'un jeton signé.
    """

    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    @transaction.atomic
    def post(
        self,
        request: Request,
    ) -> Response:
        serializer = EmailVerificationConfirmSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.validated_data["user"]

        if not user.is_email_verified:
            user.is_email_verified = True

            user.save(
                update_fields=[
                    "is_email_verified",
                    "updated_at",
                ]
            )

            reason = "email_verified"
        else:
            reason = "already_verified"

        log_security_event(
            request=request,
            event="auth.email_verification_confirm",
            outcome="success",
            reason=reason,
            user=user,
            email=user.email,
        )

        return Response(
            {
                "data": {
                    "email": user.email,
                    "isEmailVerified": True,
                },
                "message": (
                    "L'adresse e-mail est vérifiée."
                ),
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> User:
        return self.request.user
