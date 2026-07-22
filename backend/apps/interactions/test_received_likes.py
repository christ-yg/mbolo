
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profiles.models import Profile

from .models import (
    Interaction,
    InteractionDecision,
    Match,
)


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


class ReceivedLikesApiTests(APITestCase):
    def setUp(self) -> None:
        self.recipient_user, self.recipient_profile = (
            self.create_user_profile(
                email="recipient-likes@example.com",
                name="Christ",
                city="libreville",
                gender="man",
            )
        )

        self.liker_user, self.liker_profile = (
            self.create_user_profile(
                email="liker@example.com",
                name="Kevin",
                city="moanda",
                gender="woman",
            )
        )

        self.other_user, self.other_profile = (
            self.create_user_profile(
                email="other@example.com",
                name="Amina",
                city="oyem",
                gender="woman",
            )
        )

        self.received_like = Interaction.objects.create(
            actor=self.liker_user,
            target_profile=self.recipient_profile,
            decision=InteractionDecision.LIKE,
        )

        self.list_url = reverse(
            "interactions:received-like-list",
        )

        self.respond_url = reverse(
            "interactions:received-like-respond",
            kwargs={
                "interaction_id": self.received_like.id,
            },
        )

        self.client.force_authenticate(
            self.recipient_user,
        )

    def create_user_profile(
        self,
        *,
        email: str,
        name: str,
        city: str,
        gender: str,
    ):
        user = User.objects.create_user(
            email=email,
            password="StrongPassword2026!",
            is_email_verified=True,
        )

        profile = Profile.objects.create(
            user=user,
            display_name=name,
            birth_date=years_ago(29),
            gender=gender,
            city=city,
            biography="Profil complet de test.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        return user, profile

    def test_list_masks_liker_identity(self) -> None:
        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        item = response.data["results"][0]

        self.assertNotIn(
            "display_name",
            item,
        )
        self.assertNotIn(
            "profile_id",
            item,
        )
        self.assertNotIn(
            "image_url",
            item,
        )
        self.assertNotIn(
            self.liker_profile.display_name,
            str(item),
        )

        self.assertEqual(
            item["city"],
            self.liker_profile.get_city_display(),
        )

        self.assertFalse(
            item["is_identity_revealed"],
        )

    def test_list_returns_only_current_users_received_likes(
        self,
    ) -> None:
        Interaction.objects.create(
            actor=self.other_user,
            target_profile=self.liker_profile,
            decision=InteractionDecision.LIKE,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_pass_removes_received_like_from_pending_list(
        self,
    ) -> None:
        response = self.client.post(
            self.respond_url,
            {"decision": "pass"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertFalse(
            response.data["matched"],
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

    def test_like_creates_match_and_reveals_profile_only_after_match(
        self,
    ) -> None:
        response = self.client.post(
            self.respond_url,
            {"decision": "like"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            response.data["matched"],
        )
        self.assertTrue(
            response.data["match_created"],
        )
        self.assertIsNotNone(
            response.data["revealed_profile"],
        )
        self.assertEqual(
            response.data["revealed_profile"]["display_name"],
            self.liker_profile.display_name,
        )
        self.assertEqual(
            Match.objects.count(),
            1,
        )

    def test_cannot_answer_like_received_by_another_account(
        self,
    ) -> None:
        foreign_like = Interaction.objects.create(
            actor=self.other_user,
            target_profile=self.liker_profile,
            decision=InteractionDecision.LIKE,
        )

        response = self.client.post(
            reverse(
                "interactions:received-like-respond",
                kwargs={
                    "interaction_id": foreign_like.id,
                },
            ),
            {"decision": "like"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            Match.objects.count(),
            0,
        )
