from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class CurrentUserEndpointTests(TestCase):
    """
    Tests de sécurité de l'endpoint utilisateur courant.
    """

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="test-user@example.com",
            password="Temporary-Test-Password-2026!",
            is_email_verified=True,
        )

        self.url = reverse("accounts:current-user")

    def test_anonymous_user_cannot_access_endpoint(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_user_can_access_own_account(self) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            self.user.email,
        )

        self.assertEqual(
            str(response.data["id"]),
            str(self.user.id),
        )

    def test_sensitive_fields_are_not_exposed(self) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(self.url)

        forbidden_fields = {
            "password",
            "phone_number",
            "is_superuser",
            "user_permissions",
            "groups",
        }

        self.assertTrue(
            forbidden_fields.isdisjoint(response.data.keys()),
        )
