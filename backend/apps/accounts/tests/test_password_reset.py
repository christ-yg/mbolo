import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PASSWORD_RESET_TIMEOUT=1800,
)
class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reset@example.com",
            password="Ancien-Mbolo-2026!",
            is_email_verified=True,
        )

    def request_reset(self, email="reset@example.com"):
        return self.client.post(
            reverse("accounts:password-reset-request"),
            {"email": email},
            format="json",
        )

    def token_payload(self):
        body = mail.outbox[-1].body
        match = re.search(r"/reset-password\?uid=([^&\s]+)&token=([^\s]+)", body)
        self.assertIsNotNone(match)
        return match.group(1), match.group(2)

    def test_request_uses_generic_response(self):
        known = self.request_reset()
        unknown = self.request_reset("unknown@example.com")
        self.assertEqual(known.status_code, 202)
        self.assertEqual(unknown.status_code, 202)
        self.assertEqual(known.json()["message"], unknown.json()["message"])
        self.assertEqual(len(mail.outbox), 1)

    def test_valid_token_changes_password_and_is_single_use(self):
        self.request_reset()
        uid, token = self.token_payload()
        payload = {
            "uid": uid,
            "token": token,
            "password": "Nouveau-Mbolo-2026!",
            "password_confirmation": "Nouveau-Mbolo-2026!",
        }
        response = self.client.post(
            reverse("accounts:password-reset-confirm"),
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Nouveau-Mbolo-2026!"))
        replay = self.client.post(
            reverse("accounts:password-reset-confirm"),
            payload,
            format="json",
        )
        self.assertEqual(replay.status_code, 400)

    def test_invalid_token_does_not_change_password(self):
        response = self.client.post(
            reverse("accounts:password-reset-confirm"),
            {
                "uid": "invalid",
                "token": "invalid",
                "password": "Nouveau-Mbolo-2026!",
                "password_confirmation": "Nouveau-Mbolo-2026!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Ancien-Mbolo-2026!"))

    def test_csrf_is_required(self):
        csrf_client = self.client_class(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse("accounts:password-reset-request"),
            {"email": "reset@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
