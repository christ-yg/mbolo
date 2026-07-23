from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.subscriptions.models import (
    PremiumPrivacyPreference,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)

from ..presence import (
    get_user_presence,
    mark_user_offline,
    touch_user_presence,
)


User = get_user_model()


class ActivityHeartbeatTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="presence@example.com",
            password="StrongPassword123!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_can_refresh_presence(self):
        response = self.client.post(
            reverse("accounts:activity-heartbeat"),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_online"])
        self.assertIsNotNone(response.data["last_seen_at"])

    def test_mark_user_offline_is_reflected(self):
        mark_user_offline(self.user)
        presence = get_user_presence(self.user)
        self.assertFalse(presence["is_online"])
        self.assertIsNotNone(presence["last_seen_at"])

    def test_incognito_prestige_masks_public_presence(self):
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PRESTIGE,
            status=SubscriptionStatus.ACTIVE,
        )
        PremiumPrivacyPreference.objects.create(
            user=self.user,
            incognito_enabled=True,
        )
        touch_user_presence(self.user)

        presence = get_user_presence(self.user)

        self.assertFalse(presence["is_online"])
        self.assertIsNone(presence["last_seen_at"])
