from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.security_logging import log_security_event

from .serializers import (
    PaymentCheckoutCreateSerializer,
    PaymentConfirmationSerializer,
    PaymentHistorySerializer,
    PaymentMethodSerializer,
    PaymentTransactionSerializer,
    PlanSerializer,
    PremiumPrivacySerializer,
    PremiumPrivacyUpdateSerializer,
    ProfileBoostStateSerializer,
    SubscriptionStateSerializer,
)
from .services import (
    get_payment_methods,
    get_plan_catalog,
    get_privacy_state,
    get_subscription_state,
    update_incognito_preference,
    get_boost_state,
    activate_profile_boost,
    cancel_payment,
    confirm_test_payment,
    create_payment_checkout,
    get_payment_history,
    serialize_payment_transaction,
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
                    "boost": ProfileBoostStateSerializer(
                        get_boost_state(request.user)
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


class ProfileBoostView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        return Response({
            "data": ProfileBoostStateSerializer(
                get_boost_state(request.user)
            ).data
        })

    def post(self, request: Request) -> Response:
        try:
            state = activate_profile_boost(user=request.user)
        except PermissionError as exc:
            log_security_event(
                request=request,
                event="premium.boost.activate",
                outcome="failure",
                reason="premium_required",
                user=request.user,
                email=request.user.email,
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            log_security_event(
                request=request,
                event="premium.boost.activate",
                outcome="failure",
                reason="unavailable",
                user=request.user,
                email=request.user.email,
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        log_security_event(
            request=request,
            event="premium.boost.activate",
            outcome="success",
            reason="boost_activated",
            user=request.user,
            email=request.user.email,
        )
        return Response(
            {"data": ProfileBoostStateSerializer(state).data},
            status=status.HTTP_201_CREATED,
        )



class PaymentCheckoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = PaymentCheckoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = create_payment_checkout(
                user=request.user,
                plan=serializer.validated_data["plan"],
                method=serializer.validated_data["method"],
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        log_security_event(
            request=request,
            event="premium.payment.checkout.create",
            outcome="success",
            reason="transaction_created",
            user=request.user,
            email=request.user.email,
        )
        return Response(
            {
                "data": PaymentTransactionSerializer(
                    serialize_payment_transaction(payment)
                ).data
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentConfirmTestView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = PaymentConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment, _subscription = confirm_test_payment(
                user=request.user,
                transaction_id=serializer.validated_data["transaction_id"],
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except LookupError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        log_security_event(
            request=request,
            event="premium.payment.test_confirm",
            outcome="success",
            reason="server_confirmation_simulated",
            user=request.user,
            email=request.user.email,
        )
        return Response(
            {
                "data": {
                    "transaction": PaymentTransactionSerializer(
                        serialize_payment_transaction(payment)
                    ).data,
                    "subscription": SubscriptionStateSerializer(
                        get_subscription_state(request.user)
                    ).data,
                }
            }
        )


class PaymentCancelView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = PaymentConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = cancel_payment(
                user=request.user,
                transaction_id=serializer.validated_data["transaction_id"],
            )
        except LookupError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "data": PaymentTransactionSerializer(
                    serialize_payment_transaction(payment)
                ).data
            }
        )


class PaymentHistoryView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        payload = {
            "transactions": get_payment_history(request.user)
        }
        return Response(
            {
                "data": PaymentHistorySerializer(payload).data
            }
        )
