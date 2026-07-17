from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class SessionAuthenticationTests(TestCase):
    """
    Tests de sécurité de la connexion et de la déconnexion par session.
    """

    def setUp(self) -> None:
        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.login_url = reverse(
            "accounts:login",
        )

        self.logout_url = reverse(
            "accounts:logout",
        )

        self.me_url = reverse(
            "accounts:current-user",
        )

        self.password = "A-Strong-Session-Test-Password-2026!"

        self.user = User.objects.create_user(
            email="session-user@example.com",
            password=self.password,
            is_email_verified=True,
        )

    def get_csrf_token(self) -> str:
        response = self.client.get(
            self.csrf_url,
        )

        return response.data["csrfToken"]

    def login_user(self):
        csrf_token = self.get_csrf_token()

        return self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_login_requires_csrf_token(self) -> None:
        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_valid_credentials_create_session(self) -> None:
        response = self.login_user()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "sessionid",
            self.client.cookies,
        )

        me_response = self.client.get(
            self.me_url,
        )

        self.assertEqual(
            me_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            me_response.data["email"],
            self.user.email,
        )

    def test_invalid_credentials_return_generic_message(self) -> None:
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": "Incorrect-Password-2026!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        response_text = response.content.decode().lower()

        self.assertNotIn(
            "existe",
            response_text,
        )

        self.assertNotIn(
            "introuvable",
            response_text,
        )

    def test_unknown_email_uses_same_generic_failure(self) -> None:
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": "unknown@example.com",
                "password": "Incorrect-Password-2026!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "Adresse e-mail ou mot de passe incorrect.",
            response.content.decode(),
        )

    def test_suspended_user_cannot_login(self) -> None:
        self.user.is_suspended = True
        self.user.save(
            update_fields=[
                "is_suspended",
            ]
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
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_inactive_user_cannot_login(self) -> None:
        self.user.is_active = False
        self.user.save(
            update_fields=[
                "is_active",
            ]
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
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_login_rotates_session_key(self) -> None:
        csrf_token = self.get_csrf_token()

        # Force la création d'une session anonyme initiale.
        session = self.client.session
        session["anonymous_marker"] = "before-login"
        session.save()

        previous_session_key = session.session_key

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        current_session_key = self.client.session.session_key

        self.assertNotEqual(
            previous_session_key,
            current_session_key,
        )

    def test_logout_requires_authenticated_session(self) -> None:
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.logout_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_logout_requires_csrf_token(self) -> None:
        self.login_user()

        response = self.client.post(
            self.logout_url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_logout_destroys_session(self) -> None:
        login_response = self.login_user()

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        csrf_token = self.get_csrf_token()

        logout_response = self.client.post(
            self.logout_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        me_response = self.client.get(
            self.me_url,
        )

        self.assertEqual(
            me_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
