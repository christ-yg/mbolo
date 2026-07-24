from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from .models import ProfileBoost, Subscription, SubscriptionPlan


User = get_user_model()


class ProfileBoostApiTests(APITestCase):
    def setUp(self):
        self.password = "Mbolo-Boost-Secure-2026!"
        self.user = User.objects.create_user(
            email="boost@example.com",
            password=self.password,
            is_email_verified=True,
        )
        self.url = reverse("subscriptions:premium-boost")

    def test_anonymous_user_cannot_read_boost_state(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    def test_free_account_cannot_activate_boost(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProfileBoost.objects.exists())

    def test_plus_can_activate_one_thirty_minute_boost(self):
        Subscription.objects.create(user=self.user, plan=SubscriptionPlan.PLUS)
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]
        self.assertTrue(data["active"])
        self.assertEqual(data["duration_minutes"], 30)
        self.assertEqual(data["remaining"], 0)

    def test_active_boost_cannot_be_activated_twice(self):
        Subscription.objects.create(user=self.user, plan=SubscriptionPlan.PRESTIGE)
        ProfileBoost.objects.create(
            user=self.user,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(minutes=30),
        )
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(ProfileBoost.objects.filter(user=self.user).count(), 1)

    def test_prestige_receives_two_boosts_per_seven_days(self):
        Subscription.objects.create(user=self.user, plan=SubscriptionPlan.PRESTIGE)
        ProfileBoost.objects.create(
            user=self.user,
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=timezone.now() - timedelta(days=1) + timedelta(minutes=30),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["remaining"], 1)

    def test_post_requires_csrf_for_session_authentication(self):
        Subscription.objects.create(user=self.user, plan=SubscriptionPlan.PLUS)
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 403)
