from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class LoginThrottlingTests(TestCase):
    """Tests de la limitation des tentatives de connexion."""

    def setUp(self) -> None:
        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.csrf_url = reverse("core:csrf-token")
        self.login_url = reverse("accounts:login")

        self.password = "Strong-Throttle-Test-Password-2026!"

        self.user = User.objects.create_user(
            email="throttle-user@example.com",
            password=self.password,
            is_email_verified=True,
        )

    def tearDown(self) -> None:
        cache.clear()

    def get_csrf_token(self) -> str:
        response = self.client.get(self.csrf_url)
        return response.data["csrfToken"]

    def post_invalid_login(
        self,
        email: str,
        remote_addr: str = "192.0.2.10",
    ):
        csrf_token = self.get_csrf_token()

        return self.client.post(
            self.login_url,
            {
                "email": email,
                "password": "Incorrect-Password-2026!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
            REMOTE_ADDR=remote_addr,
        )

    def test_email_is_throttled_after_five_attempts(self) -> None:
        for _ in range(5):
            response = self.post_invalid_login(
                self.user.email,
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        blocked_response = self.post_invalid_login(
            self.user.email,
        )

        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

        self.assertIn(
            "Retry-After",
            blocked_response.headers,
        )

    def test_different_emails_have_separate_counters(self) -> None:
        for _ in range(5):
            self.post_invalid_login(
                "first@example.com",
            )

        response = self.post_invalid_login(
            "second@example.com",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_ip_is_throttled_across_multiple_emails(self) -> None:
        remote_addr = "192.0.2.50"

        for index in range(10):
            response = self.post_invalid_login(
                f"user-{index}@example.com",
                remote_addr=remote_addr,
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        blocked_response = self.post_invalid_login(
            "another@example.com",
            remote_addr=remote_addr,
        )

        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_successful_login_is_also_rate_limited(self) -> None:
        for _ in range(5):
            self.post_invalid_login(
                self.user.email,
            )

        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
            REMOTE_ADDR="192.0.2.10",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
