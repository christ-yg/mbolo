from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (
    PremiumPrivacyPreference,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from .services import get_privacy_state, get_subscription_state


User = get_user_model()


class PremiumFoundationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="premium@example.com",
            password="Mbolo-Premium-2026!",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_free_account_has_no_premium_entitlements(self):
        state = get_subscription_state(self.user)
        self.assertEqual(state["plan"], "free")
        self.assertFalse(state["is_premium"])
        self.assertFalse(state["entitlements"]["see_likers"])

    def test_active_plus_subscription_grants_plus_entitlements(self):
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PLUS,
            status=SubscriptionStatus.ACTIVE,
            ends_at=timezone.now() + timedelta(days=30),
        )
        state = get_subscription_state(self.user)
        self.assertTrue(state["is_premium"])
        self.assertTrue(state["entitlements"]["unlimited_likes"])
        self.assertFalse(state["entitlements"]["priority_profile"])

    def test_expired_subscription_falls_back_to_free(self):
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PRESTIGE,
            status=SubscriptionStatus.ACTIVE,
            ends_at=timezone.now() - timedelta(seconds=1),
        )
        state = get_subscription_state(self.user)
        self.assertEqual(state["plan"], "free")
        self.assertFalse(state["is_premium"])

    def test_overview_returns_catalog_and_server_entitlements(self):
        response = self.client.get(
            reverse("subscriptions:premium-overview")
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["subscription"]["plan"], "free")
        self.assertEqual(len(data["plans"]), 3)
        self.assertFalse(data["plans"][1]["payment_available"])
        self.assertEqual(data["currency"], "XAF")
        self.assertEqual(
            [item["code"] for item in data["payment_methods"]],
            ["airtel_money", "moov_money", "bank_card"],
        )
        self.assertTrue(data["payment_notice"])

    def test_overview_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(
            reverse("subscriptions:premium-overview")
        )
        self.assertIn(response.status_code, (401, 403))

    def test_free_account_cannot_enable_incognito(self):
        response = self.client.patch(
            reverse("subscriptions:premium-privacy"),
            {"incognito_enabled": True},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            PremiumPrivacyPreference.objects.filter(
                user=self.user,
                incognito_enabled=True,
            ).exists()
        )

    def test_active_prestige_can_enable_incognito(self):
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PRESTIGE,
            status=SubscriptionStatus.ACTIVE,
            ends_at=timezone.now() + timedelta(days=30),
        )
        response = self.client.patch(
            reverse("subscriptions:premium-privacy"),
            {"incognito_enabled": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["effective_incognito"])

    def test_expired_prestige_preference_has_no_effect(self):
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PRESTIGE,
            status=SubscriptionStatus.EXPIRED,
            ends_at=timezone.now() - timedelta(seconds=1),
        )
        PremiumPrivacyPreference.objects.create(
            user=self.user,
            incognito_enabled=True,
        )
        state = get_privacy_state(self.user)
        self.assertTrue(state["incognito_enabled"])
        self.assertFalse(state["incognito_available"])
        self.assertFalse(state["effective_incognito"])
