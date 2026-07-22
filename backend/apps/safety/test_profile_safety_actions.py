
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.interactions.models import Match
from apps.profiles.models import Profile

from .models import Block, Report, ReportReason


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


class ProfileSafetyActionTests(APITestCase):
    def setUp(self) -> None:
        self.actor = User.objects.create_user(
            email="safety-actor@example.com",
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
            email="safety-target@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        self.target_profile = Profile.objects.create(
            user=self.target,
            display_name="Kevin",
            birth_date=years_ago(29),
            gender="woman",
            city="moanda",
            biography="Profil cible complet.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        self.client.force_authenticate(self.actor)

        self.block_url = reverse(
            "safety:profile-block-create",
            kwargs={"profile_id": self.target_profile.id},
        )
        self.report_url = reverse(
            "safety:profile-report-create",
            kwargs={"profile_id": self.target_profile.id},
        )

    def test_profile_can_be_blocked_by_profile_uuid(self):
        response = self.client.post(
            self.block_url,
            {"confirm": True},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            Block.objects.filter(
                blocker=self.actor,
                blocked_user=self.target,
            ).exists()
        )

    def test_block_deactivates_active_match(self):
        first, second = sorted(
            (self.actor_profile, self.target_profile),
            key=lambda profile: profile.id.int,
        )

        match = Match.objects.create(
            profile_one=first,
            profile_two=second,
            is_active=True,
        )

        response = self.client.post(
            self.block_url,
            {"confirm": True},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        match.refresh_from_db()
        self.assertFalse(match.is_active)
        self.assertEqual(
            response.data["deactivated_matches"],
            1,
        )

    def test_block_requires_explicit_confirmation(self):
        response = self.client.post(
            self.block_url,
            {"confirm": False},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(Block.objects.exists())

    def test_profile_report_is_created(self):
        response = self.client.post(
            self.report_url,
            {
                "reason": ReportReason.HARASSMENT,
                "description": "Messages insistants.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            Report.objects.filter(
                reporter=self.actor,
                reported_user=self.target,
                reason=ReportReason.HARASSMENT,
            ).exists()
        )

    def test_duplicate_active_report_is_idempotent(self):
        payload = {
            "reason": ReportReason.SPAM,
            "description": "Sollicitations répétées.",
        }

        first = self.client.post(
            self.report_url,
            payload,
            format="json",
        )
        second = self.client.post(
            self.report_url,
            payload,
            format="json",
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            Report.objects.filter(
                reporter=self.actor,
                reported_user=self.target,
                reason=ReportReason.SPAM,
            ).count(),
            1,
        )

    def test_cannot_block_or_report_own_profile(self):
        own_block_url = reverse(
            "safety:profile-block-create",
            kwargs={"profile_id": self.actor_profile.id},
        )
        own_report_url = reverse(
            "safety:profile-report-create",
            kwargs={"profile_id": self.actor_profile.id},
        )

        block_response = self.client.post(
            own_block_url,
            {"confirm": True},
            format="json",
        )
        report_response = self.client.post(
            own_report_url,
            {
                "reason": ReportReason.OTHER,
                "description": "",
            },
            format="json",
        )

        self.assertEqual(
            block_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            report_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
