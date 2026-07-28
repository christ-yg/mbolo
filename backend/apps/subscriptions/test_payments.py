from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import PaymentStatus, SubscriptionPlan


@override_settings(
    MBOLO_PLUS_PRICE_XAF=5000,
    MBOLO_PRESTIGE_PRICE_XAF=10000,
    MBOLO_PAYMENT_PROVIDER="mbolo_test",
    MBOLO_PAYMENT_TEST_MODE=True,
)
class PremiumPaymentFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="premium-test@example.com",
            password="StrongPassword-2026!",
        )
        self.client.force_authenticate(self.user)

    def test_checkout_amount_is_decided_by_server(self):
        response = self.client.post(
            reverse("subscriptions:premium-payment-checkout"),
            {
                "plan": SubscriptionPlan.PLUS,
                "method": "airtel_money",
                "amount_xaf": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["amount_xaf"], 5000)
        self.assertEqual(
            response.data["data"]["status"],
            PaymentStatus.PENDING,
        )

    def test_test_confirmation_activates_subscription(self):
        checkout = self.client.post(
            reverse("subscriptions:premium-payment-checkout"),
            {
                "plan": SubscriptionPlan.PRESTIGE,
                "method": "bank_card",
            },
            format="json",
        )
        transaction_id = checkout.data["data"]["id"]

        confirmation = self.client.post(
            reverse("subscriptions:premium-payment-confirm-test"),
            {"transaction_id": transaction_id},
            format="json",
        )

        self.assertEqual(confirmation.status_code, status.HTTP_200_OK)
        self.assertEqual(
            confirmation.data["data"]["transaction"]["status"],
            PaymentStatus.SUCCEEDED,
        )
        self.assertEqual(
            confirmation.data["data"]["subscription"]["plan"],
            SubscriptionPlan.PRESTIGE,
        )

    def test_confirmation_is_idempotent(self):
        checkout = self.client.post(
            reverse("subscriptions:premium-payment-checkout"),
            {
                "plan": SubscriptionPlan.PLUS,
                "method": "moov_money",
            },
            format="json",
        )
        transaction_id = checkout.data["data"]["id"]
        url = reverse("subscriptions:premium-payment-confirm-test")

        first = self.client.post(
            url,
            {"transaction_id": transaction_id},
            format="json",
        )
        second = self.client.post(
            url,
            {"transaction_id": transaction_id},
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(
            first.data["data"]["transaction"]["id"],
            second.data["data"]["transaction"]["id"],
        )
