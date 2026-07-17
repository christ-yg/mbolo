from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail, signing
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.email_verification import (
    EMAIL_VERIFICATION_SALT,
    build_email_verification_token,
)


User = get_user_model()


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
)
class EmailVerificationTests(TestCase):
    """
    Tests fonctionnels et de sécurité de la vérification d'e-mail.

    Ces tests contrôlent notamment :

    - l'envoi du message de vérification ;
    - la confirmation avec un jeton valide ;
    - le rejet d'un jeton modifié ;
    - le rejet d'un jeton expiré ;
    - la réponse générique pour une adresse inconnue ;
    - la limitation Redis des demandes répétées ;
    - l'idempotence d'une confirmation déjà effectuée.
    """

    def setUp(self) -> None:
        """
        Prépare un environnement isolé avant chaque test.
        """

        cache.clear()
        mail.outbox.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.request_url = reverse(
            "accounts:email-verification-request",
        )

        self.confirm_url = reverse(
            "accounts:email-verification-confirm",
        )

        self.password = (
            "Strong-Email-Verification-Test-2026!"
        )

        self.user = User.objects.create_user(
            email="verification-user@example.com",
            password=self.password,
            is_email_verified=False,
        )

    def tearDown(self) -> None:
        """
        Supprime les compteurs Redis après chaque test.
        """

        cache.clear()
        mail.outbox.clear()

    def get_csrf_token(self) -> str:
        """
        Récupère le cookie et le jeton CSRF.
        """

        response = self.client.get(
            self.csrf_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "csrfToken",
            response.data,
        )

        return response.data["csrfToken"]

    def post_request(
        self,
        email: str,
        remote_addr: str = "192.0.2.10",
    ):
        """
        Envoie une demande de vérification protégée par CSRF.
        """

        csrf_token = self.get_csrf_token()

        return self.client.post(
            self.request_url,
            {
                "email": email,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
            REMOTE_ADDR=remote_addr,
        )

    def post_confirmation(
        self,
        token: str,
    ):
        """
        Confirme un jeton avec une requête CSRF valide.
        """

        csrf_token = self.get_csrf_token()

        return self.client.post(
            self.confirm_url,
            {
                "token": token,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
            REMOTE_ADDR="192.0.2.20",
        )

    def test_verification_request_requires_csrf(self) -> None:
        """
        Une demande sans jeton CSRF doit être refusée.
        """

        response = self.client.post(
            self.request_url,
            {
                "email": self.user.email,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

    def test_eligible_user_receives_verification_email(
        self,
    ) -> None:
        """
        Un compte non vérifié doit recevoir un message.
        """

        response = self.post_request(
            self.user.email,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        sent_message = mail.outbox[0]

        self.assertEqual(
            sent_message.to,
            [self.user.email],
        )

        self.assertIn(
            "Vérification",
            sent_message.subject,
        )

        self.assertIn(
            "token=",
            sent_message.body,
        )

        self.assertNotIn(
            self.password,
            sent_message.body,
        )

    def test_unknown_email_receives_generic_response(
        self,
    ) -> None:
        """
        Une adresse inconnue reçoit la même réponse HTTP,
        mais aucun e-mail n'est envoyé.
        """

        response = self.post_request(
            "unknown-user@example.com",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

        response_text = response.content.decode().lower()

        self.assertNotIn(
            "inconnu",
            response_text,
        )

        self.assertNotIn(
            "n'existe pas",
            response_text,
        )

    def test_verified_user_receives_generic_response_only(
        self,
    ) -> None:
        """
        Un compte déjà vérifié ne doit pas recevoir
        un nouveau message de vérification.
        """

        self.user.is_email_verified = True

        self.user.save(
            update_fields=[
                "is_email_verified",
            ]
        )

        response = self.post_request(
            self.user.email,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

    def test_valid_token_verifies_email(self) -> None:
        """
        Un jeton signé valide doit vérifier le compte.
        """

        token = build_email_verification_token(
            self.user,
        )

        response = self.post_confirmation(
            token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.is_email_verified,
        )

        self.assertTrue(
            response.data["data"]["isEmailVerified"],
        )

    def test_confirmation_is_idempotent(self) -> None:
        """
        Confirmer une deuxième fois le même compte
        ne doit pas provoquer d'erreur.
        """

        token = build_email_verification_token(
            self.user,
        )

        first_response = self.post_confirmation(
            token,
        )

        second_response = self.post_confirmation(
            token,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.is_email_verified,
        )

    def test_modified_token_is_rejected(self) -> None:
        """
        Toute modification du jeton doit invalider sa signature.
        """

        token = build_email_verification_token(
            self.user,
        )

        modified_token = (
            f"{token[:-1]}"
            f"{'a' if token[-1] != 'a' else 'b'}"
        )

        response = self.post_confirmation(
            modified_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.is_email_verified,
        )

    def test_token_for_changed_email_is_rejected(
        self,
    ) -> None:
        """
        Un jeton ne doit plus fonctionner si l'adresse
        du compte a été modifiée après sa création.
        """

        token = build_email_verification_token(
            self.user,
        )

        self.user.email = "changed-email@example.com"

        self.user.save(
            update_fields=[
                "email",
            ]
        )

        response = self.post_confirmation(
            token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.is_email_verified,
        )

    def test_expired_token_is_rejected(self) -> None:
        """
        Un jeton dont la signature est considérée expirée
        doit être rejeté.
        """

        token = build_email_verification_token(
            self.user,
        )

        expired_exception = signing.SignatureExpired(
            "Expired test token"
        )

        with patch(
            "apps.accounts.email_verification.signing.loads",
            side_effect=expired_exception,
        ):
            response = self.post_confirmation(
                token,
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "expiré",
            response.content.decode().lower(),
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.is_email_verified,
        )

    def test_token_does_not_contain_password(self) -> None:
        """
        Le jeton ne doit jamais contenir le mot de passe.
        """

        token = build_email_verification_token(
            self.user,
        )

        self.assertNotIn(
            self.password,
            token,
        )

        payload = signing.loads(
            token,
            salt=EMAIL_VERIFICATION_SALT,
        )

        self.assertNotIn(
            "password",
            payload,
        )

        self.assertNotIn(
            "sessionid",
            payload,
        )

        self.assertNotIn(
            "csrf",
            payload,
        )

    def test_request_is_throttled_after_three_attempts(
        self,
    ) -> None:
        """
        Une quatrième demande pour le même e-mail
        doit être bloquée par Redis.
        """

        for _ in range(3):
            response = self.post_request(
                self.user.email,
                remote_addr="192.0.2.50",
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_202_ACCEPTED,
            )

        blocked_response = self.post_request(
            self.user.email,
            remote_addr="192.0.2.50",
        )

        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

        self.assertIn(
            "Retry-After",
            blocked_response.headers,
        )
