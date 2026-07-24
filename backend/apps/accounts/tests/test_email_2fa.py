import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class EmailTwoFactorTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.password = "Mbolo-Deux-Facteurs-2026!"
        self.user = User.objects.create_user(
            email="deux-facteurs@example.com",
            password=self.password,
            is_email_verified=True,
        )

    def tearDown(self):
        cache.clear()

    def test_disabled_account_uses_normal_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get(reverse("accounts:current-user")).status_code,
            200,
        )

    def test_settings_require_current_password(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("accounts:email-2fa-settings"),
            {"current_password": "incorrect", "enabled": True},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_2fa_enabled)

    def test_login_requires_valid_email_code_when_enabled(self):
        self.user.email_2fa_enabled = True
        self.user.save(update_fields=["email_2fa_enabled", "updated_at"])
        response = self.client.post(
            reverse("accounts:login"),
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("requiresTwoFactor", response.json()["data"])
        self.assertIn(
            self.client.get(reverse("accounts:current-user")).status_code,
            (401, 403),
        )

        code = re.search(r"\b(\d{6})\b", mail.outbox[0].body).group(1)
        confirmation = self.client.post(
            reverse("accounts:login-2fa-confirm"),
            {
                "challenge_token": response.json()["data"]["challengeToken"],
                "code": code,
            },
            format="json",
        )
        self.assertEqual(confirmation.status_code, 200)
        self.assertEqual(
            self.client.get(reverse("accounts:current-user")).status_code,
            200,
        )

    def test_wrong_code_does_not_create_session(self):
        self.user.email_2fa_enabled = True
        self.user.save(update_fields=["email_2fa_enabled", "updated_at"])
        response = self.client.post(
            reverse("accounts:login"),
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        confirmation = self.client.post(
            reverse("accounts:login-2fa-confirm"),
            {
                "challenge_token": response.json()["data"]["challengeToken"],
                "code": "000000",
            },
            format="json",
        )
        self.assertEqual(confirmation.status_code, 400)
