from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.security_logging import log_security_event

from .serializers import (
    PaymentMethodSerializer,
    PlanSerializer,
    PremiumPrivacySerializer,
    PremiumPrivacyUpdateSerializer,
    SubscriptionStateSerializer,
)
from .services import (
    get_payment_methods,
    get_plan_catalog,
    get_privacy_state,
    get_subscription_state,
    update_incognito_preference,
)


class PremiumOverviewView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        state = SubscriptionStateSerializer(
            get_subscription_state(request.user)
        ).data
        plans = PlanSerializer(get_plan_catalog(), many=True).data
        methods = PaymentMethodSerializer(
            get_payment_methods(), many=True
        ).data
        return Response(
            {
                "data": {
                    "subscription": state,
                    "plans": plans,
                    "payment_methods": methods,
                    "currency": "XAF",
                    "payment_notice": (
                        "Les paiements réels restent verrouillés tant que le "
                        "contrat marchand, les tarifs et les clés du "
                        "prestataire ne sont pas configurés."
                    ),
                    "privacy": PremiumPrivacySerializer(
                        get_privacy_state(request.user)
                    ).data,
                }
            }
        )


class PremiumPrivacyView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request: Request) -> Response:
        serializer = PremiumPrivacyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            state = update_incognito_preference(
                user=request.user,
                enabled=serializer.validated_data["incognito_enabled"],
            )
        except PermissionError as exc:
            log_security_event(
                request=request,
                event="premium.incognito.update",
                outcome="failure",
                reason="prestige_required",
                user=request.user,
                email=request.user.email,
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        log_security_event(
            request=request,
            event="premium.incognito.update",
            outcome="success",
            reason=(
                "enabled"
                if state["effective_incognito"]
                else "disabled"
            ),
            user=request.user,
            email=request.user.email,
        )
        return Response(
            {"data": PremiumPrivacySerializer(state).data}
        )
