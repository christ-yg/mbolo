from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class CSRFTokenEndpointTests(TestCase):
    """Tests de récupération du jeton CSRF."""

    def setUp(self) -> None:
        self.client = APIClient(
            enforce_csrf_checks=True,
        )

    def test_csrf_endpoint_returns_token_and_cookie(self) -> None:
        response = self.client.get(
            reverse("core:csrf-token"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "csrfToken",
            response.data,
        )

        self.assertIn(
            "csrftoken",
            response.cookies,
        )
