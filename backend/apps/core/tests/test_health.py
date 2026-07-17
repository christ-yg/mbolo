from django.test import TestCase
from django.urls import reverse
from rest_framework import status


class HealthCheckTests(TestCase):
    """
    Tests de l'endpoint public de contrôle de santé.
    """

    def test_health_endpoint_is_public(self) -> None:
        response = self.client.get(
            reverse("core:health"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.json(),
            {"status": "ok"},
        )

    def test_health_endpoint_does_not_leak_technical_details(self) -> None:
        response = self.client.get(
            reverse("core:health"),
        )

        response_body = response.json()

        forbidden_keys = {
            "django_version",
            "database_version",
            "hostname",
            "environment",
            "secret_key",
            "debug",
        }

        self.assertTrue(
            forbidden_keys.isdisjoint(response_body.keys()),
        )
