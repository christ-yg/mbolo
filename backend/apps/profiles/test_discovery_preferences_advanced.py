
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.photos.models import ProfilePhoto

from .models import Profile, SearchPreferences


User = get_user_model()


def years_ago(years: int) -> date:
    today = date.today()

    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(
            year=today.year - years,
            month=2,
            day=28,
        )


class AdvancedDiscoveryPreferencesTests(APITestCase):
    def setUp(self) -> None:
        self.actor = User.objects.create_user(
            email="preferences-actor@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        Profile.objects.create(
            user=self.actor,
            display_name="Christ",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil acteur complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        self.with_photo_user = User.objects.create_user(
            email="with-photo@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        self.with_photo_profile = Profile.objects.create(
            user=self.with_photo_user,
            display_name="Kevin",
            birth_date=years_ago(28),
            gender="woman",
            city="moanda",
            biography="Profil avec photo.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        self.without_photo_user = User.objects.create_user(
            email="without-photo@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        self.without_photo_profile = Profile.objects.create(
            user=self.without_photo_user,
            display_name="Amina",
            birth_date=years_ago(27),
            gender="woman",
            city="oyem",
            biography="Profil sans photo.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        self.preferences_url = reverse(
            "profiles:current-search-preferences",
        )
        self.discovery_url = reverse(
            "profiles:discovery",
        )

        self.client.force_authenticate(self.actor)

    def test_preferences_endpoint_exposes_photo_filter(self):
        response = self.client.get(self.preferences_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn(
            "only_profiles_with_photos",
            response.data,
        )
        self.assertFalse(
            response.data["only_profiles_with_photos"],
        )

    def test_preferences_can_be_updated(self):
        response = self.client.patch(
            self.preferences_url,
            {
                "minimum_age": 25,
                "maximum_age": 35,
                "preferred_genders": ["woman"],
                "preferred_cities": ["moanda", "oyem"],
                "preferred_dating_intents": ["friendship"],
                "only_verified_profiles": True,
                "only_profiles_with_photos": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        preferences = SearchPreferences.objects.get(
            user=self.actor,
        )

        self.assertTrue(
            preferences.only_profiles_with_photos,
        )
        self.assertEqual(
            preferences.minimum_age,
            25,
        )

    def test_photo_filter_excludes_profiles_without_photos(self):
        SearchPreferences.objects.update_or_create(
            user=self.actor,
            defaults={
                "minimum_age": 18,
                "maximum_age": 45,
                "preferred_genders": [],
                "preferred_cities": [],
                "preferred_dating_intents": [],
                "only_verified_profiles": True,
                "only_profiles_with_photos": True,
            },
        )

        ProfilePhoto.objects.create(
            profile=self.with_photo_profile,
            image="profiles/test-photo.jpg",
            position=1,
            is_primary=True,
        )

        response = self.client.get(self.discovery_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertIn(
            str(self.with_photo_profile.id),
            returned_ids,
        )
        self.assertNotIn(
            str(self.without_photo_profile.id),
            returned_ids,
        )

    def test_invalid_age_range_is_rejected(self):
        response = self.client.patch(
            self.preferences_url,
            {
                "minimum_age": 40,
                "maximum_age": 25,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
