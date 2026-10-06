from unittest.mock import Mock, patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .ebilling import EbillingCheckout
from .models import PaymentStatus, SubscriptionPlan


@override_settings(
    MBOLO_PLUS_PRICE_XAF=5000,
    MBOLO_PRESTIGE_PRICE_XAF=10000,
    MBOLO_PAYMENT_PROVIDER="ebilling",
    MBOLO_PAYMENT_TEST_MODE=False,
    EBILLING_BASE_URL="https://lab.billing-easy.net",
    EBILLING_CLIENT_ID="test-client",
    EBILLING_CLIENT_SECRET="test-secret",
    EBILLING_HTTP_TIMEOUT_SECONDS=5,
)
class EbillingPremiumFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ebilling-test@example.com",
            password="StrongPassword-2026!",
        )
        self.client.force_authenticate(self.user)

    @patch("apps.subscriptions.services.EbillingClient")
    def test_airtel_checkout_stores_provider_references(self, client_cls):
        client = client_cls.return_value
        client.initiate_mobile_money.return_value = EbillingCheckout(
            bill_id="bill-123",
            ussd_push_id="push-456",
        )

        response = self.client.post(
            reverse("subscriptions:premium-payment-checkout"),
            {
                "plan": SubscriptionPlan.PLUS,
                "method": "airtel_money",
                "payer_phone": "077123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["provider"], "ebilling")
        self.assertEqual(response.data["data"]["provider_bill_id"], "bill-123")
        self.assertEqual(
            response.data["data"]["provider_ussd_push_id"],
            "push-456",
        )
        client.initiate_mobile_money.assert_called_once()

    def test_mobile_money_checkout_requires_phone(self):
        response = self.client.post(
            reverse("subscriptions:premium-payment-checkout"),
            {
                "plan": SubscriptionPlan.PLUS,
                "method": "moov_money",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.subscriptions.services.EbillingClient")
    def test_refresh_paid_transaction_activates_subscription(self, client_cls):
        client = client_cls.return_value
        client.initiate_mobile_money.return_value = EbillingCheckout(
            bill_id="bill-789",
            ussd_push_id="push-paid",
        )
        client.get_ussd_push_status.return_value = {"state": "paid"}

        checkout = self.client.post(
            reverse("subscriptions:premium-payment-checkout"),
            {
                "plan": SubscriptionPlan.PRESTIGE,
                "method": "airtel_money",
                "payer_phone": "074123456",
            },
            format="json",
        )
        transaction_id = checkout.data["data"]["id"]

        refreshed = self.client.post(
            reverse("subscriptions:premium-payment-refresh"),
            {"transaction_id": transaction_id},
            format="json",
        )

        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertEqual(
            refreshed.data["data"]["status"],
            PaymentStatus.SUCCEEDED,
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription.plan, SubscriptionPlan.PRESTIGE)

    @patch("apps.subscriptions.services.EbillingClient")
    def test_webhook_requeries_provider_instead_of_trusting_body(self, client_cls):
        client = client_cls.return_value
        client.initiate_mobile_money.return_value = EbillingCheckout(
            bill_id="bill-webhook",
            ussd_push_id="push-webhook",
        )
        client.get_ussd_push_status.return_value = {"state": "pending"}

        checkout = self.client.post(
            reverse("subscriptions:premium-payment-checkout"),
            {
                "plan": SubscriptionPlan.PLUS,
                "method": "airtel_money",
                "payer_phone": "077123456",
            },
            format="json",
        )
        reference = checkout.data["data"]["provider_reference"]

        self.client.force_authenticate(user=None)
        webhook = self.client.post(
            reverse("subscriptions:premium-payment-ebilling-webhook"),
            {
                "reference": reference,
                "state": "paid",
            },
            format="json",
        )

        self.assertEqual(webhook.status_code, status.HTTP_200_OK)
        self.assertFalse(
            self.user.premium_payments.filter(
                status=PaymentStatus.SUCCEEDED
            ).exists()
        )
        client.get_ussd_push_status.assert_called_once_with("push-webhook")
