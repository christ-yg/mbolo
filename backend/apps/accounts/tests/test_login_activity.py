from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import LoginActivity


User = get_user_model()


class LoginActivityTests(APITestCase):
    password = "Mbolo-Activite-Test-2026!"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="activity.member@example.com",
            password=self.password,
            is_email_verified=True,
        )
        self.other_user = User.objects.create_user(
            email="other.member@example.com",
            password=self.password,
            is_email_verified=True,
        )

    def test_successful_login_records_minimal_activity(self) -> None:
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
            ),
            REMOTE_ADDR="203.0.113.42",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        activity = LoginActivity.objects.get(user=self.user)
        self.assertEqual(activity.method, "password")
        self.assertEqual(activity.device, "Chrome · Windows")
        self.assertTrue(activity.ip_fingerprint)
        self.assertNotEqual(activity.ip_fingerprint, "203.0.113.42")

    def test_endpoint_returns_only_current_users_activity(self) -> None:
        own_activity = LoginActivity.objects.create(
            user=self.user,
            method="password",
            device="Firefox · Linux",
            ip_fingerprint="abcd1234",
        )
        other_activity = LoginActivity.objects.create(
            user=self.other_user,
            method="email_2fa",
            device="Edge · Windows",
            ip_fingerprint="secret999",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("accounts:login-activity"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()["data"]
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["id"], str(own_activity.id))
        self.assertNotIn(str(other_activity.id), str(body))
        self.assertNotIn(self.user.email, str(body))

    def test_endpoint_requires_authentication(self) -> None:
        response = self.client.get(
            reverse("accounts:login-activity"),
        )

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_only_fifty_latest_activities_are_retained(self) -> None:
        from apps.accounts.login_activity import record_login_activity

        request = self.client.get("/").wsgi_request
        request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 Firefox/128 Linux"
        for _ in range(52):
            record_login_activity(
                request=request,
                user=self.user,
                method="password",
            )

        self.assertEqual(
            LoginActivity.objects.filter(user=self.user).count(),
            50,
        )
