from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.test import APITestCase


User = get_user_model()


class AccountSecurityTests(APITestCase):
    def setUp(self):
        self.password = "Mbolo-Ancien-2026!"
        self.user = User.objects.create_user(
            email="security@example.com",
            password=self.password,
            is_email_verified=True,
        )
        self.client.force_login(self.user)

    def test_change_password_keeps_current_session(self):
        response = self.client.post(
            reverse("accounts:change-password"),
            {
                "current_password": self.password,
                "new_password": "Mbolo-Nouveau-2026!",
                "new_password_confirmation": "Mbolo-Nouveau-2026!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Mbolo-Nouveau-2026!"))
        current = self.client.get(reverse("accounts:current-user"))
        self.assertEqual(current.status_code, 200)

    def test_wrong_current_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:revoke-other-sessions"),
            {"current_password": "Mot-de-passe-incorrect"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_revoke_other_sessions_keeps_current_session(self):
        other_client = Client()
        other_client.force_login(self.user)
        old_session_key = other_client.session.session_key
        response = self.client.post(
            reverse("accounts:revoke-other-sessions"),
            {"current_password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(
            response.json()["data"]["revokedSessions"],
            1,
        )
        self.assertNotEqual(old_session_key, self.client.session.session_key)
        current = self.client.get(reverse("accounts:current-user"))
        self.assertEqual(current.status_code, 200)

    def test_deactivation_closes_session(self):
        response = self.client.post(
            reverse("accounts:deactivate-account"),
            {
                "current_password": self.password,
                "confirmation": "DESACTIVER",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        current = self.client.get(reverse("accounts:current-user"))
        self.assertIn(current.status_code, (401, 403))

    def test_sensitive_actions_require_csrf(self):
        csrf_client = self.client_class(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        response = csrf_client.post(
            reverse("accounts:revoke-other-sessions"),
            {"current_password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
