from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.subscriptions.models import Subscription, SubscriptionPlan

from .discovery import build_discovery_queryset
from .locations import (
    approximate_city_distance_km,
    public_distance_label,
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


class PrivacyFriendlyDistanceTests(TestCase):
    """Vérifie le calcul, le filtrage Premium et la minimisation publique."""

    def setUp(self):
        self.actor = User.objects.create_user(
            email="distance-actor@example.com",
            password="StrongDistance2026!",
            is_email_verified=True,
        )
        Profile.objects.create(
            user=self.actor,
            display_name="Acteur",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )
        Subscription.objects.create(
            user=self.actor,
            plan=SubscriptionPlan.PLUS,
        )
        SearchPreferences.objects.create(
            user=self.actor,
            minimum_age=18,
            maximum_age=45,
            maximum_distance_km=50,
        )

    def create_candidate(self, email: str, city: str) -> Profile:
        user = User.objects.create_user(
            email=email,
            password="StrongCandidate2026!",
            is_email_verified=True,
        )
        return Profile.objects.create(
            user=user,
            display_name=city,
            birth_date=years_ago(28),
            gender="woman",
            city=city,
            biography="Profil complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

    def test_same_city_is_inside_fifty_kilometres(self):
        nearby = self.create_candidate(
            "nearby@example.com",
            "libreville",
        )
        result_ids = set(
            build_discovery_queryset(user=self.actor).values_list(
                "id",
                flat=True,
            )
        )
        self.assertIn(nearby.id, result_ids)

    def test_distant_city_is_excluded(self):
        distant = self.create_candidate(
            "distant@example.com",
            "franceville",
        )
        result_ids = set(
            build_discovery_queryset(user=self.actor).values_list(
                "id",
                flat=True,
            )
        )
        self.assertNotIn(distant.id, result_ids)

    def test_unknown_city_never_receives_invented_distance(self):
        self.assertIsNone(
            approximate_city_distance_km(
                "libreville",
                "other",
            )
        )

    def test_public_label_is_rounded(self):
        self.assertEqual(
            public_distance_label(4),
            "Moins de 10 km",
        )
        self.assertEqual(
            public_distance_label(47),
            "Environ 50 km",
        )
