from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class RegistrationEndpointTests(TestCase):
    """Tests fonctionnels et de sécurité de l'inscription."""

    def setUp(self) -> None:
        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.registration_url = reverse(
            "accounts:register",
        )

        self.valid_payload = {
            "email": "New.User@Example.COM",
            "password": "A-Very-Strong-Test-Password-2026!",
            "password_confirmation": (
                "A-Very-Strong-Test-Password-2026!"
            ),
        }

    def get_csrf_token(self) -> str:
        response = self.client.get(
            self.csrf_url,
        )

        return response.data["csrfToken"]

    def test_registration_requires_csrf_token(self) -> None:
        response = self.client.post(
            self.registration_url,
            self.valid_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            User.objects.count(),
            0,
        )

    def test_user_can_register_with_valid_data(self) -> None:
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.registration_url,
            self.valid_payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            User.objects.count(),
            1,
        )

        user = User.objects.get()

        self.assertEqual(
            user.email,
            "new.user@example.com",
        )

        self.assertFalse(
            user.is_email_verified,
        )

        self.assertTrue(
            user.check_password(
                self.valid_payload["password"]
            )
        )

    def test_password_confirmation_must_match(self) -> None:
        csrf_token = self.get_csrf_token()

        payload = {
            **self.valid_payload,
            "password_confirmation": (
                "Another-Strong-Test-Password-2026!"
            ),
        }

        response = self.client.post(
            self.registration_url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            User.objects.count(),
            0,
        )

    def test_weak_password_is_rejected(self) -> None:
        csrf_token = self.get_csrf_token()

        payload = {
            "email": "user@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        }

        response = self.client.post(
            self.registration_url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            User.objects.count(),
            0,
        )

    def test_duplicate_email_is_rejected(self) -> None:
        User.objects.create_user(
            email="existing@example.com",
            password="Existing-Strong-Test-Password-2026!",
        )

        csrf_token = self.get_csrf_token()

        payload = {
            "email": "EXISTING@example.com",
            "password": "Another-Strong-Test-Password-2026!",
            "password_confirmation": (
                "Another-Strong-Test-Password-2026!"
            ),
        }

        response = self.client.post(
            self.registration_url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            User.objects.count(),
            1,
        )

    def test_password_is_never_returned(self) -> None:
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.registration_url,
            self.valid_payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        response_text = response.content.decode()

        self.assertNotIn(
            self.valid_payload["password"],
            response_text,
        )

        self.assertNotIn(
            "password_confirmation",
            response.data,
        )
