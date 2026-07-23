from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.subscriptions.models import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)

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


class PremiumDiscoveryFiltersTests(TestCase):
    """
    Garantit que React ne constitue jamais la source de vérité des droits.

    Le serveur autorise gratuitement l'âge et le genre, mais réserve les
    villes, intentions, distance et filtres de qualité à Plus/Prestige.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="premium-filters@example.com",
            password="StrongPremiumFilters2026!",
            is_email_verified=True,
        )
        Profile.objects.create(
            user=self.user,
            display_name="Acteur",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )
        self.preferences = SearchPreferences.objects.create(
            user=self.user,
            minimum_age=18,
            maximum_age=45,
            preferred_genders=[],
            preferred_cities=["libreville"],
            preferred_dating_intents=["serious_relationship"],
            only_profiles_with_photos=True,
        )
        self.candidate = self._candidate(
            email="candidate@example.com",
            city="oyem",
            intent="friendship",
        )
        self.preferences_url = reverse(
            "profiles:current-search-preferences"
        )
        self.discovery_url = reverse("profiles:discovery")
        self.client.force_authenticate(self.user)

    def _candidate(self, *, email: str, city: str, intent: str) -> Profile:
        candidate_user = User.objects.create_user(
            email=email,
            password="StrongCandidate2026!",
            is_email_verified=True,
        )
        return Profile.objects.create(
            user=candidate_user,
            display_name="Candidate",
            birth_date=years_ago(28),
            gender="woman",
            city=city,
            biography="Profil candidat complet.",
            dating_intent=intent,
            is_discoverable=True,
        )

    def _result_ids(self) -> set[str]:
        response = self.client.get(self.discovery_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {item["id"] for item in response.data["results"]}

    def test_free_user_can_update_basic_filters(self):
        response = self.client.patch(
            self.preferences_url,
            {
                "minimum_age": 24,
                "maximum_age": 36,
                "preferred_genders": ["woman"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["advanced_filters_available"])

    def test_free_user_cannot_change_advanced_filters(self):
        response = self.client.patch(
            self.preferences_url,
            {"preferred_cities": ["oyem"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("preferred_cities", response.data)

    def test_free_user_stored_advanced_filters_are_ignored(self):
        self.assertIn(str(self.candidate.id), self._result_ids())

    def test_active_plus_applies_stored_advanced_filters(self):
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PLUS,
            status=SubscriptionStatus.ACTIVE,
        )
        self.assertNotIn(str(self.candidate.id), self._result_ids())

    def test_expired_plus_preserves_but_stops_applying_filters(self):
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PLUS,
            status=SubscriptionStatus.ACTIVE,
            ends_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertIn(str(self.candidate.id), self._result_ids())
        self.preferences.refresh_from_db()
        self.assertEqual(self.preferences.preferred_cities, ["libreville"])
