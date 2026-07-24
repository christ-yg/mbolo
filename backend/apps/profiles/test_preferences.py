from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.subscriptions.models import Subscription, SubscriptionPlan

from .models import SearchPreferences


User = get_user_model()


class SearchPreferencesEndpointTests(TestCase):
    """
    Tests fonctionnels et de sécurité des préférences privées.
    """

    def setUp(self) -> None:
        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.preferences_url = reverse(
            "profiles:current-search-preferences",
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.user = User.objects.create_user(
            email="preferences-user@example.com",
            password=(
                "Strong-Preferences-Password-2026!"
            ),
            is_email_verified=True,
        )
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PLUS,
        )

    def tearDown(self) -> None:
        cache.clear()

    def authenticate(self) -> str:
        self.client.force_login(
            self.user,
        )

        response = self.client.get(
            self.csrf_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.data["csrfToken"]

    def patch_preferences(
        self,
        payload: dict,
        csrf_token: str,
    ):
        return self.client.patch(
            self.preferences_url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_anonymous_user_cannot_access_preferences(
        self,
    ) -> None:
        response = self.client.get(
            self.preferences_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            SearchPreferences.objects.count(),
            0,
        )

    def test_first_get_creates_default_preferences(
        self,
    ) -> None:
        self.authenticate()

        response = self.client.get(
            self.preferences_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            SearchPreferences.objects.count(),
            1,
        )

        self.assertEqual(
            response.data["minimum_age"],
            18,
        )

        self.assertEqual(
            response.data["maximum_age"],
            45,
        )

        self.assertEqual(
            response.data["maximum_distance_km"],
            50,
        )

        self.assertFalse(
            response.data["only_verified_profiles"],
        )

    def test_user_can_update_valid_preferences(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        response = self.patch_preferences(
            {
                "minimum_age": 25,
                "maximum_age": 40,
                "preferred_genders": [
                    "woman",
                ],
                "preferred_cities": [
                    "libreville",
                    "port_gentil",
                ],
                "preferred_dating_intents": [
                    "serious_relationship",
                    "marriage",
                ],
                "maximum_distance_km": 100,
                "only_verified_profiles": True,
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        preferences = SearchPreferences.objects.get(
            user=self.user,
        )

        self.assertEqual(
            preferences.minimum_age,
            25,
        )

        self.assertEqual(
            preferences.maximum_age,
            40,
        )

        self.assertEqual(
            preferences.preferred_genders,
            ["woman"],
        )

        self.assertEqual(
            preferences.maximum_distance_km,
            100,
        )

    def test_minimum_age_cannot_be_below_eighteen(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        response = self.patch_preferences(
            {
                "minimum_age": 17,
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "minimum_age",
            response.data,
        )

    def test_maximum_age_must_not_be_lower_than_minimum(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        response = self.patch_preferences(
            {
                "minimum_age": 40,
                "maximum_age": 30,
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "maximum_age",
            response.data,
        )

    def test_invalid_gender_is_rejected(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        response = self.patch_preferences(
            {
                "preferred_genders": [
                    "invalid-value",
                ],
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "preferred_genders",
            response.data,
        )

    def test_invalid_city_is_rejected(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        response = self.patch_preferences(
            {
                "preferred_cities": [
                    "paris",
                ],
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "preferred_cities",
            response.data,
        )

    def test_duplicate_choices_are_rejected(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        response = self.patch_preferences(
            {
                "preferred_cities": [
                    "libreville",
                    "libreville",
                ],
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_distance_cannot_exceed_five_hundred(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        response = self.patch_preferences(
            {
                "maximum_distance_km": 501,
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "maximum_distance_km",
            response.data,
        )

    def test_patch_requires_csrf_token(
        self,
    ) -> None:
        self.client.force_login(
            self.user,
        )

        response = self.client.patch(
            self.preferences_url,
            {
                "minimum_age": 25,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_client_cannot_replace_preferences_id(
        self,
    ) -> None:
        csrf_token = self.authenticate()

        first_response = self.client.get(
            self.preferences_url,
        )

        original_id = str(
            first_response.data["id"]
        )

        response = self.patch_preferences(
            {
                "id": (
                    "00000000-0000-0000-0000-000000000001"
                ),
                "minimum_age": 22,
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            str(response.data["id"]),
            original_id,
        )

    def test_users_cannot_read_each_others_preferences(
        self,
    ) -> None:
        first_preferences = (
            SearchPreferences.objects.create(
                user=self.user,
                minimum_age=20,
                maximum_age=30,
            )
        )

        second_user = User.objects.create_user(
            email="second-preferences@example.com",
            password=(
                "Strong-Preferences-Password-2026!"
            ),
            is_email_verified=True,
        )

        second_preferences = (
            SearchPreferences.objects.create(
                user=second_user,
                minimum_age=35,
                maximum_age=50,
            )
        )

        self.client.force_login(
            second_user,
        )

        response = self.client.get(
            self.preferences_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            str(response.data["id"]),
            str(second_preferences.id),
        )

        self.assertNotEqual(
            str(response.data["id"]),
            str(first_preferences.id),
        )

        self.assertEqual(
            response.data["minimum_age"],
            35,
        )
