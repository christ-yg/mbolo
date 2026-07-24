from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountSecurityEvent
from apps.core.security_logging import log_security_event


User = get_user_model()


class AccountSecurityEventTests(APITestCase):
    password = "Mbolo-Historique-Securite-2026!"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="security.history@example.com",
            password=self.password,
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_allowed_event_is_persisted_without_sensitive_data(self) -> None:
        request = self.client.post(
            reverse("accounts:activity-heartbeat"),
            {},
            format="json",
        ).wsgi_request

        log_security_event(
            request=request,
            event="auth.sessions_revoke",
            outcome="success",
            reason="other_sessions_revoked",
            user=self.user,
            email=self.user.email,
        )

        event = AccountSecurityEvent.objects.get(user=self.user)

        self.assertEqual(event.event, "auth.sessions_revoke")
        self.assertEqual(event.outcome, "success")
        self.assertEqual(event.reason, "other_sessions_revoked")

        model_values = {
            field.name
            for field in AccountSecurityEvent._meta.get_fields()
        }
        self.assertNotIn("ip", model_values)
        self.assertNotIn("email", model_values)
        self.assertNotIn("path", model_values)
        self.assertNotIn("user_agent", model_values)

    def test_unrelated_event_is_not_persisted(self) -> None:
        request = self.client.post(
            reverse("accounts:activity-heartbeat"),
            {},
            format="json",
        ).wsgi_request

        log_security_event(
            request=request,
            event="profile.discovery",
            outcome="success",
            reason="discovery_requested",
            user=self.user,
            email=self.user.email,
        )

        self.assertFalse(
            AccountSecurityEvent.objects.filter(user=self.user).exists()
        )

    def test_api_requires_authentication(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse("accounts:security-events"),
        )

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_member_only_receives_own_events(self) -> None:
        other_user = User.objects.create_user(
            email="other.security@example.com",
            password=self.password,
        )

        own_event = AccountSecurityEvent.objects.create(
            user=self.user,
            event="auth.password_change",
            outcome="success",
            reason="password_changed",
        )
        AccountSecurityEvent.objects.create(
            user=other_user,
            event="auth.sessions_revoke",
            outcome="success",
            reason="other_sessions_revoked",
        )

        response = self.client.get(
            reverse("accounts:security-events"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], str(own_event.id))

    def test_password_change_automatically_creates_history(self) -> None:
        self.client.force_authenticate(user=None)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:change-password"),
            {
                "current_password": self.password,
                "new_password": "Mbolo-Nouveau-Securite-2027!",
                "new_password_confirmation": (
                    "Mbolo-Nouveau-Securite-2027!"
                ),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AccountSecurityEvent.objects.filter(
                user=self.user,
                event="auth.password_change",
                outcome="success",
            ).exists()
        )

    def test_only_last_one_hundred_events_are_retained(self) -> None:
        request = self.client.post(
            reverse("accounts:activity-heartbeat"),
            {},
            format="json",
        ).wsgi_request

        for _ in range(105):
            log_security_event(
                request=request,
                event="auth.sessions_revoke",
                outcome="success",
                reason="other_sessions_revoked",
                user=self.user,
                email=self.user.email,
            )

        self.assertEqual(
            AccountSecurityEvent.objects.filter(user=self.user).count(),
            100,
        )
