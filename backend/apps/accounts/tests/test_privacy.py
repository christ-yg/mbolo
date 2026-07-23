from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


User = get_user_model()


class PrivacyCenterTests(APITestCase):
    def setUp(self):
        self.password = "Mbolo-Privacy-2026!"
        self.user = User.objects.create_user(
            email="privacy@example.com",
            password=self.password,
            is_email_verified=True,
        )
        self.client.force_login(self.user)

    def test_export_is_downloadable_and_contains_no_password(self):
        response = self.client.get(
            reverse("accounts:personal-data-export")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment;", response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("privacy@example.com", content)
        self.assertNotIn(self.user.password, content)
        self.assertNotIn("_auth_user_hash", content)
        self.assertEqual(response["Cache-Control"], "no-store, private")

    def test_export_requires_authentication(self):
        self.client.logout()
        response = self.client.get(
            reverse("accounts:personal-data-export")
        )
        self.assertIn(response.status_code, (401, 403))

    def test_delete_requires_exact_confirmation(self):
        response = self.client.post(
            reverse("accounts:permanent-account-delete"),
            {
                "current_password": self.password,
                "confirmation": "SUPPRIMER",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_removes_account_and_session(self):
        user_id = self.user.pk
        response = self.client.post(
            reverse("accounts:permanent-account-delete"),
            {
                "current_password": self.password,
                "confirmation": "SUPPRIMER DEFINITIVEMENT",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        current = self.client.get(reverse("accounts:current-user"))
        self.assertIn(current.status_code, (401, 403))

    def test_delete_requires_csrf(self):
        csrf_client = self.client_class(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        response = csrf_client.post(
            reverse("accounts:permanent-account-delete"),
            {
                "current_password": self.password,
                "confirmation": "SUPPRIMER DEFINITIVEMENT",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
