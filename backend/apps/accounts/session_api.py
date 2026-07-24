"""
API de gestion individuelle des appareils connectés.
"""

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event

from .models import AccountSession
from .session_registry import (
    hash_session_key,
    remove_stale_account_sessions,
    revoke_registered_session,
)


class RevokeAccountSessionSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Le mot de passe actuel est incorrect."
            )

        return value


class AccountSessionListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        remove_stale_account_sessions(user=request.user)

        current_hash = (
            hash_session_key(request.session.session_key)
            if request.session.session_key
            else None
        )

        sessions = request.user.account_sessions.all()[:30]

        return Response(
            {
                "data": [
                    {
                        "id": str(account_session.id),
                        "device": account_session.device,
                        "ipFingerprint": account_session.ip_fingerprint,
                        "createdAt": (
                            account_session.created_at.isoformat()
                        ),
                        "lastSeenAt": (
                            account_session.last_seen_at.isoformat()
                        ),
                        "isCurrent": (
                            account_session.session_key_hash
                            == current_hash
                        ),
                    }
                    for account_session in sessions
                ]
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class AccountSessionRevokeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(
        self,
        request: Request,
        session_id: str,
    ) -> Response:
        serializer = RevokeAccountSessionSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        try:
            account_session = request.user.account_sessions.get(
                id=session_id,
            )
        except AccountSession.DoesNotExist:
            return Response(
                {"detail": "Cette session n'existe plus."},
                status=status.HTTP_404_NOT_FOUND,
            )

        revoked = revoke_registered_session(
            user=request.user,
            account_session=account_session,
            current_session_key=request.session.session_key,
        )

        if not revoked:
            return Response(
                {
                    "detail": (
                        "La session actuelle ne peut pas être fermée ici."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_security_event(
            request=request,
            event="auth.session_revoke_one",
            outcome="success",
            reason="selected_session_revoked",
            user=request.user,
            email=request.user.email,
        )

        return Response(
            {"message": "L'appareil sélectionné a été déconnecté."},
            status=status.HTTP_200_OK,
        )
