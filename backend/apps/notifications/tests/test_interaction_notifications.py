
"""
Tests des notifications produites par les likes et les matchs.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.profiles.models import Profile

from apps.interactions.models import (
    Interaction,
    InteractionDecision,
)


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


class LikeAndMatchNotificationTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.interaction_url = reverse(
            "interactions:interaction-create",
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.password = (
            "Strong-Like-Match-Notification-Password-2026!"
        )

        self.actor_user, self.actor_profile = (
            self.create_user_and_profile(
                email="actor-notification@example.com",
                display_name="Christ",
                gender="man",
            )
        )

        self.target_user, self.target_profile = (
            self.create_user_and_profile(
                email="target-notification@example.com",
                display_name="Kevin",
                gender="woman",
            )
        )

    def tearDown(self) -> None:
        cache.clear()

    def create_user_and_profile(
        self,
        *,
        email: str,
        display_name: str,
        gender: str,
    ):
        user = User.objects.create_user(
            email=email,
            password=self.password,
            is_email_verified=True,
        )

        profile = Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=years_ago(30),
            gender=gender,
            city="libreville",
            biography="Profil complet utilisé pour les tests.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        return user, profile

    def authenticate_actor(self) -> str:
        self.client.force_login(self.actor_user)

        response = self.client.get(self.csrf_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.data["csrfToken"]

    def post_like(self, *, csrf_token: str):
        return self.client.post(
            self.interaction_url,
            {
                "target_profile_id": str(
                    self.target_profile.id
                ),
                "decision": "like",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_non_reciprocal_like_creates_anonymous_notification(
        self,
    ) -> None:
        csrf_token = self.authenticate_actor()

        response = self.post_like(
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        notification = Notification.objects.get(
            recipient=self.target_user,
            kind=Notification.Kind.LIKE,
        )

        self.assertEqual(
            notification.title,
            "Quelqu’un a aimé ton profil",
        )

        self.assertNotIn(
            self.actor_profile.display_name,
            notification.title,
        )

        self.assertNotIn(
            self.actor_profile.display_name,
            notification.body,
        )

    def test_repeated_like_does_not_duplicate_notification(
        self,
    ) -> None:
        csrf_token = self.authenticate_actor()

        first_response = self.post_like(
            csrf_token=csrf_token,
        )

        second_response = self.post_like(
            csrf_token=csrf_token,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.target_user,
                kind=Notification.Kind.LIKE,
            ).count(),
            1,
        )

    def test_mutual_like_creates_one_match_notification_per_user(
        self,
    ) -> None:
        Interaction.objects.create(
            actor=self.target_user,
            target_profile=self.actor_profile,
            decision=InteractionDecision.LIKE,
        )

        csrf_token = self.authenticate_actor()

        response = self.post_like(
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(response.data["matched"])
        self.assertTrue(response.data["match_created"])

        actor_notification = Notification.objects.get(
            recipient=self.actor_user,
            kind=Notification.Kind.MATCH,
        )

        target_notification = Notification.objects.get(
            recipient=self.target_user,
            kind=Notification.Kind.MATCH,
        )

        self.assertIn(
            self.target_profile.display_name,
            actor_notification.title,
        )

        self.assertIn(
            self.actor_profile.display_name,
            target_notification.title,
        )

        self.assertEqual(
            actor_notification.target_path,
            "/matches",
        )

        self.assertEqual(
            target_notification.target_path,
            "/matches",
        )

        self.assertFalse(
            Notification.objects.filter(
                kind=Notification.Kind.LIKE,
            ).exists()
        )
