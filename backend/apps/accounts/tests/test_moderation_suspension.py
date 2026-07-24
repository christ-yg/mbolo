from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class ModerationSuspensionAuthenticationTests(TestCase):
    """
    Vérifie qu'une sanction agit aussi sur une session déjà ouverte.
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="moderation-session@example.com",
            password="Strong-Moderation-Test-2026!",
            is_email_verified=True,
        )
        self.client = APIClient()
        self.client.force_login(self.user)
        self.me_url = reverse("accounts:current-user")

    def test_active_suspension_blocks_existing_session(self) -> None:
        self.user.is_suspended = True
        self.user.suspension_until = timezone.now() + timedelta(days=7)
        self.user.save(
            update_fields=("is_suspended", "suspension_until", "updated_at")
        )

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_expired_suspension_is_lifted_automatically(self) -> None:
        self.user.is_suspended = True
        self.user.suspension_until = timezone.now() - timedelta(seconds=1)
        self.user.save(
            update_fields=("is_suspended", "suspension_until", "updated_at")
        )

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_suspended)
        self.assertIsNone(self.user.suspension_until)

    def test_permanent_suspension_blocks_existing_session(self) -> None:
        self.user.is_suspended = True
        self.user.suspension_until = None
        self.user.save(
            update_fields=("is_suspended", "suspension_until", "updated_at")
        )

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
