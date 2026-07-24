import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class SecurityLoggingTests(TestCase):
    """
    Tests de la journalisation des événements d'authentification.

    Les tests vérifient notamment :
    - la présence des événements ;
    - leur format JSON ;
    - la pseudonymisation des données ;
    - l'absence de mots de passe ;
    - la journalisation des blocages Redis.
    """

    def setUp(self) -> None:
        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.register_url = reverse(
            "accounts:register",
        )

        self.login_url = reverse(
            "accounts:login",
        )

        self.logout_url = reverse(
            "accounts:logout",
        )

        self.password = (
            "Strong-Security-Logging-Password-2026!"
        )

        self.user = User.objects.create_user(
            email="logging-user@example.com",
            password=self.password,
            is_email_verified=True,
        )

    def tearDown(self) -> None:
        cache.clear()

    def get_csrf_token(self) -> str:
        response = self.client.get(
            self.csrf_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.data[
            "csrfToken"
        ]

    @staticmethod
    def parse_last_event(
        log_context,
    ) -> dict:
        """
        Convertit le dernier message du logger en dictionnaire JSON.
        """

        message = (
            log_context.records[-1]
            .getMessage()
        )

        return json.loads(
            message
        )

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
            REMOTE_ADDR="192.0.2.10",
        )

    def test_successful_login_is_logged(self) -> None:
        """
        Une connexion réussie doit générer un événement structuré.
        """

        with self.assertLogs(
            "mbolo.security",
            level="INFO",
        ) as log_context:
            response = self.login_user()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        event = self.parse_last_event(
            log_context
        )

        self.assertEqual(
            event["event"],
            "auth.login",
        )

        self.assertEqual(
            event["outcome"],
            "success",
        )

        self.assertEqual(
            event["reason"],
            "authenticated",
        )

        self.assertEqual(
            event["user_id"],
            str(self.user.id),
        )

        self.assertIsNotNone(
            event["email_hash"],
        )

        self.assertIsNotNone(
            event["ip_hash"],
        )

    def test_failed_login_is_logged_without_password(self) -> None:
        """
        Une connexion refusée doit être journalisée sans mot de passe.
        """

        csrf_token = self.get_csrf_token()

        incorrect_password = (
            "Incorrect-Security-Password-2026!"
        )

        with self.assertLogs(
            "mbolo.security",
            level="INFO",
        ) as log_context:
            response = self.client.post(
                self.login_url,
                {
                    "email": self.user.email,
                    "password": incorrect_password,
                },
                format="json",
                HTTP_X_CSRFTOKEN=csrf_token,
                REMOTE_ADDR="192.0.2.20",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        event = self.parse_last_event(
            log_context
        )

        self.assertEqual(
            event["event"],
            "auth.login",
        )

        self.assertEqual(
            event["outcome"],
            "failure",
        )

        self.assertEqual(
            event["reason"],
            "invalid_credentials",
        )

        serialized_event = json.dumps(
            event
        )

        self.assertNotIn(
            incorrect_password,
            serialized_event,
        )

        self.assertNotIn(
            self.user.email,
            serialized_event,
        )

        self.assertNotIn(
            "192.0.2.20",
            serialized_event,
        )

    def test_registration_is_logged_without_plain_email(self) -> None:
        """
        Une inscription réussie doit générer un événement pseudonymisé.
        """

        csrf_token = self.get_csrf_token()

        registration_email = (
            "new-logging-user@example.com"
        )

        registration_password = (
            "Strong-Registration-Logging-2026!"
        )

        with self.assertLogs(
            "mbolo.security",
            level="INFO",
        ) as log_context:
            response = self.client.post(
                self.register_url,
                {
                    "email": registration_email,
                    "password": registration_password,
                    "password_confirmation": (
                        registration_password
                    ),
                    "accept_terms": True,
                    "confirm_adult": True,
                },
                format="json",
                HTTP_X_CSRFTOKEN=csrf_token,
                REMOTE_ADDR="192.0.2.30",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        event = self.parse_last_event(
            log_context
        )

        self.assertEqual(
            event["event"],
            "auth.register",
        )

        self.assertEqual(
            event["outcome"],
            "success",
        )

        serialized_event = json.dumps(
            event
        )

        self.assertNotIn(
            registration_email,
            serialized_event,
        )

        self.assertNotIn(
            registration_password,
            serialized_event,
        )

    def test_logout_is_logged_before_session_destruction(self) -> None:
        """
        La déconnexion doit conserver l'identifiant utilisateur
        dans l'événement avant de détruire la session.
        """

        login_response = self.login_user()

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        csrf_token = self.get_csrf_token()

        with self.assertLogs(
            "mbolo.security",
            level="INFO",
        ) as log_context:
            response = self.client.post(
                self.logout_url,
                {},
                format="json",
                HTTP_X_CSRFTOKEN=csrf_token,
                REMOTE_ADDR="192.0.2.40",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        event = self.parse_last_event(
            log_context
        )

        self.assertEqual(
            event["event"],
            "auth.logout",
        )

        self.assertEqual(
            event["outcome"],
            "success",
        )

        self.assertEqual(
            event["user_id"],
            str(self.user.id),
        )

    def test_rate_limited_login_is_logged(self) -> None:
        """
        La sixième tentative visant le même e-mail doit être bloquée
        et produire un événement auth.login / blocked.
        """

        for _ in range(5):
            csrf_token = self.get_csrf_token()

            response = self.client.post(
                self.login_url,
                {
                    "email": self.user.email,
                    "password": (
                        "Incorrect-Password-2026!"
                    ),
                },
                format="json",
                HTTP_X_CSRFTOKEN=csrf_token,
                REMOTE_ADDR="192.0.2.50",
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        csrf_token = self.get_csrf_token()

        with self.assertLogs(
            "mbolo.security",
            level="INFO",
        ) as log_context:
            blocked_response = self.client.post(
                self.login_url,
                {
                    "email": self.user.email,
                    "password": (
                        "Incorrect-Password-2026!"
                    ),
                },
                format="json",
                HTTP_X_CSRFTOKEN=csrf_token,
                REMOTE_ADDR="192.0.2.50",
            )

        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

        event = self.parse_last_event(
            log_context
        )

        self.assertEqual(
            event["event"],
            "auth.login",
        )

        self.assertEqual(
            event["outcome"],
            "blocked",
        )

        self.assertEqual(
            event["reason"],
            "rate_limited",
        )
