"""
API des préférences d'alertes de connexion Mbolo.

La notification interne de sécurité est obligatoire et ne peut pas être
désactivée. Seul le canal e-mail est configurable.

Toute modification exige le mot de passe actuel afin de limiter le risque
qu'une session momentanément accessible soit utilisée pour couper les alertes.
"""

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event


class LoginAlertEmailPreferenceSerializer(serializers.Serializer):
    """
    Valide la préférence et réauthentifie le membre.
    """

    current_password = serializers.CharField(
        max_length=128,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    enabled = serializers.BooleanField()

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Le mot de passe actuel est incorrect."
            )

        return value


@method_decorator(csrf_protect, name="dispatch")
class LoginAlertEmailPreferenceView(APIView):
    """
    Consulte ou modifie le canal e-mail des alertes de connexion.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        return Response(
            {
                "data": {
                    "loginAlertEmailsEnabled": (
                        request.user.login_alert_emails_enabled
                    ),
                    "internalSecurityNotificationsEnabled": True,
                }
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request: Request) -> Response:
        serializer = LoginAlertEmailPreferenceSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        enabled = serializer.validated_data["enabled"]
        user = request.user

        user.login_alert_emails_enabled = enabled
        user.save(
            update_fields=(
                "login_alert_emails_enabled",
                "updated_at",
            )
        )

        log_security_event(
            request=request,
            event="auth.login_alert_email_preference",
            outcome="success",
            reason="enabled" if enabled else "disabled",
            user=user,
            email=user.email,
        )

        return Response(
            {
                "data": {
                    "loginAlertEmailsEnabled": enabled,
                    "internalSecurityNotificationsEnabled": True,
                },
                "message": (
                    "Les alertes de connexion par e-mail sont activées."
                    if enabled
                    else (
                        "Les alertes par e-mail sont désactivées. "
                        "Les notifications internes restent actives."
                    )
                ),
            },
            status=status.HTTP_200_OK,
        )
