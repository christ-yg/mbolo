from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import LoginActivity
from apps.accounts.login_alerts import notify_unrecognized_login
from apps.notifications.models import Notification


User = get_user_model()


class LoginAlertEmailPreferenceTests(APITestCase):
    password = "Mbolo-Preference-Alerte-2026!"

    def setUp(self) -> None:
        cache.clear()
        self.user = User.objects.create_user(
            email="preference.alert@example.com",
            password=self.password,
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        cache.clear()
        super().tearDown()

    def test_default_preference_is_enabled(self) -> None:
        self.assertTrue(self.user.login_alert_emails_enabled)

        response = self.client.get(
            reverse("accounts:login-alert-email-preference"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.json()["data"]["loginAlertEmailsEnabled"]
        )
        self.assertTrue(
            response.json()["data"][
                "internalSecurityNotificationsEnabled"
            ]
        )

    def test_update_requires_authentication(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.patch(
            reverse("accounts:login-alert-email-preference"),
            {
                "current_password": self.password,
                "enabled": False,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_wrong_password_is_rejected(self) -> None:
        response = self.client.patch(
            reverse("accounts:login-alert-email-preference"),
            {
                "current_password": "Mauvais-mot-de-passe!",
                "enabled": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.login_alert_emails_enabled)

    def test_member_can_disable_email_channel(self) -> None:
        response = self.client.patch(
            reverse("accounts:login-alert-email-preference"),
            {
                "current_password": self.password,
                "enabled": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.login_alert_emails_enabled)
        self.assertTrue(
            response.json()["data"][
                "internalSecurityNotificationsEnabled"
            ]
        )

    @patch(
        "apps.accounts.login_alerts.broadcast_notification_created"
    )
    def test_internal_alert_remains_when_email_is_disabled(
        self,
        mocked_broadcast,
    ) -> None:
        self.user.login_alert_emails_enabled = False
        self.user.save(
            update_fields=(
                "login_alert_emails_enabled",
                "updated_at",
            )
        )

        activity = LoginActivity.objects.create(
            user=self.user,
            method="password",
            device="Firefox · Linux",
            ip_fingerprint="abcdef123456",
        )

        notification = notify_unrecognized_login(
            user=self.user,
            activity=activity,
        )

        self.assertTrue(
            Notification.objects.filter(id=notification.id).exists()
        )
        mocked_broadcast.assert_called_once()
        self.assertEqual(len(mail.outbox), 0)

    def test_email_is_sent_when_preference_is_enabled(self) -> None:
        activity = LoginActivity.objects.create(
            user=self.user,
            method="password",
            device="Chrome · Windows",
            ip_fingerprint="123456abcdef",
        )

        notify_unrecognized_login(
            user=self.user,
            activity=activity,
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(
            activity.ip_fingerprint,
            mail.outbox[0].body,
        )
