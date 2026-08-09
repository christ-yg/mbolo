from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
)
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
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
from .email_2fa import (
    InvalidTwoFactorChallenge,
    consume_email_two_factor_challenge,
    create_email_two_factor_challenge,
)
from .password_reset import send_password_reset_message
from .privacy import (
    build_personal_data_export,
    permanently_delete_account,
)
from .session_security import revoke_other_sessions
from .models import User
from .login_activity import record_login_activity
from .presence import (
    mark_user_offline,
    touch_user_presence,
)
from .serializers import (
    CurrentUserSerializer,
    ChangePasswordSerializer,
    CurrentPasswordSerializer,
    DeactivateAccountSerializer,
    DeleteAccountSerializer,
    EmailVerificationConfirmSerializer,
    EmailVerificationRequestSerializer,
    EmailTwoFactorConfirmSerializer,
    EmailTwoFactorSettingsSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
)
from .throttles import (
    EmailTwoFactorChallengeThrottle,
    EmailTwoFactorConfirmIPThrottle,
    EmailVerificationRequestEmailThrottle,
    EmailVerificationRequestIPThrottle,
    LoginEmailThrottle,
    LoginIPThrottle,
    PasswordResetConfirmIPThrottle,
    PasswordResetRequestEmailThrottle,
    PasswordResetRequestIPThrottle,
    RegistrationIPThrottle,
)


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)
    throttle_classes = (RegistrationIPThrottle,)

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

        if user.email_2fa_enabled:
            challenge_token, masked_email = (
                create_email_two_factor_challenge(user)
            )
            log_security_event(
                request=request,
                event="auth.login_2fa_challenge",
                outcome="success",
                reason="code_sent",
                user=user,
                email=user.email,
            )
            return Response(
                {
                    "data": {
                        "requiresTwoFactor": True,
                        "challengeToken": challenge_token,
                        "maskedEmail": masked_email,
                    },
                    "message": (
                        "Un code temporaire a été envoyé par e-mail."
                    ),
                },
                status=status.HTTP_202_ACCEPTED,
            )

        login(request, user)
        touch_user_presence(user)
        record_login_activity(
            request=request,
            user=user,
            method="password",
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
class EmailTwoFactorConfirmView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)
    throttle_classes = (
        EmailTwoFactorConfirmIPThrottle,
        EmailTwoFactorChallengeThrottle,
    )

    def post(self, request: Request) -> Response:
        serializer = EmailTwoFactorConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = consume_email_two_factor_challenge(
                challenge_token=serializer.validated_data["challenge_token"],
                code=serializer.validated_data["code"],
            )
        except InvalidTwoFactorChallenge as exc:
            log_security_event(
                request=request,
                event="auth.login_2fa_confirm",
                outcome="failure",
                reason="invalid_or_expired_code",
            )
            raise ValidationError(
                {"code": "Ce code est invalide ou a expiré."}
            ) from exc

        login(request, user)
        touch_user_presence(user)
        record_login_activity(
            request=request,
            user=user,
            method="email_2fa",
        )
        log_security_event(
            request=request,
            event="auth.login_2fa_confirm",
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
                    "isEmailVerified": user.is_email_verified,
                    "emailTwoFactorEnabled": user.email_2fa_enabled,
                },
                "message": "Connexion confirmée.",
            },
            status=status.HTTP_200_OK,
        )


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

        mark_user_offline(current_user)
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


class ActivityHeartbeatView(APIView):
    """Actualise la présence du compte authentifié."""

    permission_classes = (IsAuthenticated,)

    def post(
        self,
        request: Request,
    ) -> Response:
        presence = touch_user_presence(request.user)

        return Response(
            {
                "is_online": presence["is_online"],
                "last_seen_at": presence["last_seen_at"],
            },
            status=status.HTTP_200_OK,
        )


class LoginActivityListView(APIView):
    """Retourne uniquement l'historique du membre authentifié."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        activities = request.user.login_activities.all()[:20]
        return Response(
            {
                "data": [
                    {
                        "id": str(activity.id),
                        "method": activity.method,
                        "device": activity.device,
                        "ipFingerprint": activity.ip_fingerprint,
                        "createdAt": activity.created_at.isoformat(),
                    }
                    for activity in activities
                ]
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> User:
        touch_user_presence(self.request.user)
        return self.request.user


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)
    throttle_classes = (
        PasswordResetRequestIPThrottle,
        PasswordResetRequestEmailThrottle,
    )

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(
            email=email,
            is_active=True,
            is_suspended=False,
        ).first()

        if user is not None:
            send_password_reset_message(user=user)
            reason = "message_sent"
        else:
            reason = "generic_response"

        log_security_event(
            request=request,
            event="auth.password_reset_request",
            outcome="accepted",
            reason=reason,
            user=user,
            email=email,
        )
        return Response(
            {
                "message": (
                    "Si un compte éligible correspond à cette adresse, "
                    "un lien de réinitialisation sera envoyé."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)
    throttle_classes = (PasswordResetConfirmIPThrottle,)

    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            log_security_event(
                request=request,
                event="auth.password_reset_confirm",
                outcome="failure",
                reason="invalid_or_expired_token",
            )
            raise

        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password", "updated_at"])
        log_security_event(
            request=request,
            event="auth.password_reset_confirm",
            outcome="success",
            reason="password_changed",
            user=user,
            email=user.email,
        )
        return Response(
            {"message": "Ton mot de passe a été modifié. Tu peux te connecter."},
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])

        # Conserve uniquement la session utilisée pour cette opération.
        update_session_auth_hash(request, user)
        revoked = revoke_other_sessions(
            user=user,
            current_session_key=request.session.session_key,
        )
        log_security_event(
            request=request,
            event="auth.password_change",
            outcome="success",
            reason="password_changed",
            user=user,
            email=user.email,
        )
        return Response(
            {
                "message": (
                    "Mot de passe modifié. Les autres sessions "
                    "ont été déconnectées."
                ),
                "data": {"revokedSessions": revoked},
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class RevokeOtherSessionsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = CurrentPasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        revoked = revoke_other_sessions(
            user=request.user,
            current_session_key=request.session.session_key,
        )
        log_security_event(
            request=request,
            event="auth.sessions_revoke",
            outcome="success",
            reason="other_sessions_revoked",
            user=request.user,
            email=request.user.email,
        )
        return Response(
            {
                "message": "Les autres sessions ont été déconnectées.",
                "data": {"revokedSessions": revoked},
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class EmailTwoFactorSettingsView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request: Request) -> Response:
        serializer = EmailTwoFactorSettingsSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        enabled = serializer.validated_data["enabled"]
        if enabled and not user.is_email_verified:
            raise ValidationError(
                {
                    "enabled": (
                        "Vérifie d’abord ton adresse e-mail avant "
                        "d’activer la double authentification."
                    )
                }
            )
        user.email_2fa_enabled = enabled
        user.save(update_fields=["email_2fa_enabled", "updated_at"])
        log_security_event(
            request=request,
            event="auth.email_2fa_settings",
            outcome="success",
            reason="enabled" if enabled else "disabled",
            user=user,
            email=user.email,
        )
        return Response(
            {
                "data": {"emailTwoFactorEnabled": enabled},
                "message": (
                    "Double authentification activée."
                    if enabled
                    else "Double authentification désactivée."
                ),
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class DeactivateAccountView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = DeactivateAccountSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        log_security_event(
            request=request,
            event="auth.account_deactivate",
            outcome="success",
            reason="account_deactivated",
            user=user,
            email=user.email,
        )
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None
        if profile is not None and profile.is_discoverable:
            profile.is_discoverable = False
            profile.save(update_fields=["is_discoverable", "updated_at"])
        revoke_other_sessions(
            user=user,
            current_session_key=request.session.session_key,
        )
        mark_user_offline(user)
        logout(request)
        return Response(
            {
                "message": (
                    "Ton compte est désactivé et toutes les sessions "
                    "sont fermées."
                )
            },
            status=status.HTTP_200_OK,
        )


class PersonalDataExportView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> JsonResponse:
        payload = build_personal_data_export(request.user)
        log_security_event(
            request=request,
            event="privacy.data_export",
            outcome="success",
            reason="export_downloaded",
            user=request.user,
            email=request.user.email,
        )
        response = JsonResponse(
            payload,
            json_dumps_params={
                "ensure_ascii": False,
                "indent": 2,
            },
        )
        response["Content-Disposition"] = (
            'attachment; filename="mbolo-mes-donnees.json"'
        )
        response["Cache-Control"] = "no-store, private"
        response["X-Content-Type-Options"] = "nosniff"
        return response


@method_decorator(csrf_protect, name="dispatch")
class PermanentAccountDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = DeleteAccountSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        log_security_event(
            request=request,
            event="privacy.account_delete",
            outcome="success",
            reason="account_permanently_deleted",
            user=user,
            email=user.email,
        )
        mark_user_offline(user)
        permanently_delete_account(user)
        request.session.flush()
        return Response(
            {
                "message": (
                    "Le compte et ses données personnelles "
                    "ont été supprimés définitivement."
                )
            },
            status=status.HTTP_200_OK,
        )
