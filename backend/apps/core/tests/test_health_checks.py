from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse


class HealthCheckTests(SimpleTestCase):
    """Vérifie les contrats publics de liveness et de readiness."""

    def test_liveness_confirms_that_django_responds(self) -> None:
        response = self.client.get(reverse("core:health-live"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("apps.core.views._cache_is_ready", return_value=True)
    @patch("apps.core.views._database_is_ready", return_value=True)
    def test_readiness_succeeds_when_dependencies_are_ready(
        self, database_ready, cache_ready
    ) -> None:
        response = self.client.get(reverse("core:health-ready"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("apps.core.views._cache_is_ready", return_value=True)
    @patch("apps.core.views._database_is_ready", return_value=False)
    def test_readiness_fails_when_postgresql_is_unavailable(
        self, database_ready, cache_ready
    ) -> None:
        response = self.client.get(reverse("core:health-ready"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})

    @patch("apps.core.views._cache_is_ready", return_value=False)
    @patch("apps.core.views._database_is_ready", return_value=True)
    def test_readiness_fails_when_redis_is_unavailable(
        self, database_ready, cache_ready
    ) -> None:
        response = self.client.get(reverse("core:health-ready"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})

    @patch("apps.core.views._cache_is_ready", return_value=True)
    @patch("apps.core.views._database_is_ready", return_value=True)
    def test_legacy_health_route_keeps_working(
        self, database_ready, cache_ready
    ) -> None:
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
