from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.profiles.models import Profile
from apps.subscriptions.models import Subscription, SubscriptionPlan

from .models import Interaction, InteractionDecision


User = get_user_model()


def years_ago(years: int) -> date:
    today = date.today()
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(
            year=today.year - years,
            month=2,
            day=28,
        )


class PremiumRewindTests(TestCase):
    """
    Tests fonctionnels et de sécurité du Rewind Mbolo Plus/Prestige.
    """

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.rewind_url = reverse("interactions:interaction-rewind")
        self.interaction_url = reverse("interactions:interaction-create")
        self.discovery_url = reverse("profiles:discovery")
        self.csrf_url = reverse("core:csrf-token")

        self.actor = User.objects.create_user(
            email="rewind-actor@example.com",
            password="StrongRewindActor2026!",
            is_email_verified=True,
        )
        Profile.objects.create(
            user=self.actor,
            display_name="Acteur Rewind",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil acteur complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )
        self.target = self._create_target(
            email="rewind-target@example.com",
            display_name="Profil restaurable",
        )

    def tearDown(self) -> None:
        cache.clear()

    def _create_target(self, *, email: str, display_name: str) -> Profile:
        user = User.objects.create_user(
            email=email,
            password="StrongRewindTarget2026!",
            is_email_verified=True,
        )
        return Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=years_ago(28),
            gender="woman",
            city="libreville",
            biography="Profil cible complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

    def _authenticate(self) -> str:
        self.client.force_login(self.actor)
        response = self.client.get(self.csrf_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["csrfToken"]

    def _post_pass(self, *, profile: Profile, csrf_token: str):
        return self.client.post(
            self.interaction_url,
            {
                "target_profile_id": str(profile.id),
                "decision": InteractionDecision.PASS,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_anonymous_user_cannot_read_rewind_state(self):
        response = self.client.get(self.rewind_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_free_account_cannot_rewind(self):
        csrf_token = self._authenticate()
        self._post_pass(profile=self.target, csrf_token=csrf_token)

        response = self.client.post(
            self.rewind_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            Interaction.objects.filter(
                actor=self.actor,
                target_profile=self.target,
                decision=InteractionDecision.PASS,
            ).exists()
        )

    def test_active_plus_can_restore_last_pass(self):
        Subscription.objects.create(
            user=self.actor,
            plan=SubscriptionPlan.PLUS,
        )
        csrf_token = self._authenticate()
        self._post_pass(profile=self.target, csrf_token=csrf_token)

        excluded_response = self.client.get(self.discovery_url)
        excluded_ids = {
            item["id"] for item in excluded_response.data["results"]
        }
        self.assertNotIn(str(self.target.id), excluded_ids)

        response = self.client.post(
            self.rewind_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["rewound"])
        self.assertEqual(response.data["profile"]["id"], str(self.target.id))
        self.assertFalse(
            Interaction.objects.filter(
                actor=self.actor,
                target_profile=self.target,
            ).exists()
        )

        restored_response = self.client.get(self.discovery_url)
        restored_ids = {
            item["id"] for item in restored_response.data["results"]
        }
        self.assertIn(str(self.target.id), restored_ids)

    def test_rewind_refuses_when_latest_action_is_like(self):
        Subscription.objects.create(
            user=self.actor,
            plan=SubscriptionPlan.PLUS,
        )
        older_target = self._create_target(
            email="older-pass@example.com",
            display_name="Ancien pass",
        )
        csrf_token = self._authenticate()
        self._post_pass(profile=older_target, csrf_token=csrf_token)
        self.client.post(
            self.interaction_url,
            {
                "target_profile_id": str(self.target.id),
                "decision": InteractionDecision.LIKE,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        response = self.client.post(
            self.rewind_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            Interaction.objects.filter(
                actor=self.actor,
                target_profile=older_target,
                decision=InteractionDecision.PASS,
            ).exists()
        )

    def test_rewind_post_requires_csrf(self):
        Subscription.objects.create(
            user=self.actor,
            plan=SubscriptionPlan.PLUS,
        )
        self.client.force_login(self.actor)

        response = self.client.post(
            self.rewind_url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_state_exposes_right_without_private_history(self):
        Subscription.objects.create(
            user=self.actor,
            plan=SubscriptionPlan.PRESTIGE,
        )
        csrf_token = self._authenticate()
        self._post_pass(profile=self.target, csrf_token=csrf_token)

        response = self.client.get(self.rewind_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data),
            {"entitled", "available", "reason"},
        )
        self.assertTrue(response.data["entitled"])
        self.assertTrue(response.data["available"])
