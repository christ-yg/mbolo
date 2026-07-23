from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    PaymentMethodSerializer,
    PlanSerializer,
    SubscriptionStateSerializer,
)
from .services import (
    get_payment_methods,
    get_plan_catalog,
    get_subscription_state,
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
                }
            }
        )
