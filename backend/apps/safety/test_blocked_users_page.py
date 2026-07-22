
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profiles.models import Profile

from .models import Block


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


class BlockedUsersPageApiTests(APITestCase):
    def setUp(self) -> None:
        self.actor = User.objects.create_user(
            email="blocked-actor@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        Profile.objects.create(
            user=self.actor,
            display_name="Christ",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil acteur.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        self.target = User.objects.create_user(
            email="blocked-target@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        self.target_profile = Profile.objects.create(
            user=self.target,
            display_name="Kevin",
            birth_date=years_ago(29),
            gender="woman",
            city="moanda",
            biography="Profil cible.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        self.other = User.objects.create_user(
            email="blocked-other@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        Profile.objects.create(
            user=self.other,
            display_name="Amina",
            birth_date=years_ago(27),
            gender="woman",
            city="oyem",
            biography="Autre profil.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        self.block = Block.objects.create(
            blocker=self.actor,
            blocked_user=self.target,
        )
        self.foreign_block = Block.objects.create(
            blocker=self.other,
            blocked_user=self.target,
        )

        self.client.force_authenticate(self.actor)

    def test_list_is_scoped_and_minimized(self):
        response = self.client.get(
            reverse("safety:block-list-create")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        item = response.data["results"][0]
        self.assertEqual(item["id"], str(self.block.id))
        self.assertEqual(
            item["blocked_profile"]["display_name"],
            self.target_profile.display_name,
        )
        self.assertNotIn("email", item["blocked_profile"])
        self.assertNotIn("birth_date", item["blocked_profile"])

    def test_owner_can_unblock(self):
        response = self.client.delete(
            reverse(
                "safety:block-delete",
                kwargs={"block_id": self.block.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            Block.objects.filter(id=self.block.id).exists()
        )

    def test_unblock_idor_is_rejected(self):
        response = self.client.delete(
            reverse(
                "safety:block-delete",
                kwargs={"block_id": self.foreign_block.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertTrue(
            Block.objects.filter(
                id=self.foreign_block.id
            ).exists()
        )
