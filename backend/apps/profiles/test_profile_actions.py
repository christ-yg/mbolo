
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.interactions.models import (
    Interaction,
    InteractionDecision,
)
from apps.profiles.models import Profile


User = get_user_model()


def years_ago(years: int) -> date:
    today = date.today()

    try:
        return today.replace(
            year=today.year - years,
        )
    except ValueError:
        return today.replace(
            year=today.year - years,
            month=2,
            day=28,
        )


class PublicProfileActionStateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.actor = User.objects.create_user(
            email="profile-action-actor@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )

        self.actor_profile = Profile.objects.create(
            user=self.actor,
            display_name="Christ",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil acteur complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        self.target = User.objects.create_user(
            email="profile-action-target@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )

        self.target_profile = Profile.objects.create(
            user=self.target,
            display_name="Alex",
            birth_date=years_ago(28),
            gender="non_binary",
            city="lambarene",
            biography="Profil cible complet.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        self.client.force_authenticate(self.actor)

        self.url = reverse(
            "profiles:public-profile-detail",
            kwargs={
                "profile_id": self.target_profile.id,
            },
        )

    def test_detail_returns_human_readable_labels(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["city_label"],
            "Lambaréné",
        )

        self.assertEqual(
            response.data["dating_intent_label"],
            "Amitié",
        )

        self.assertEqual(
            response.data["gender_label"],
            "Non binaire",
        )

    def test_current_decision_is_null_before_interaction(self):
        response = self.client.get(self.url)

        self.assertIsNone(
            response.data["current_decision"],
        )

    def test_current_decision_reflects_existing_like(self):
        Interaction.objects.create(
            actor=self.actor,
            target_profile=self.target_profile,
            decision=InteractionDecision.LIKE,
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.data["current_decision"],
            "like",
        )
