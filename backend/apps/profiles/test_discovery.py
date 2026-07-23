from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.subscriptions.models import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)

from .models import (
    Profile,
    SearchPreferences,
)


User = get_user_model()


def years_ago(
    years: int,
) -> date:
    """
    Retourne une date correspondant à un âge précis.

    Le cas du 29 février est traité pour que les tests
    fonctionnent toutes les années.
    """

    today = date.today()

    try:
        return today.replace(
            year=today.year - years,
        )
    except ValueError:
        return today.replace(
            year=today.year - years,
            month=2,
            day=28,
        )


class DiscoveryEndpointTests(TestCase):
    """
    Tests fonctionnels et de sécurité du moteur de découverte.
    """

    def setUp(self) -> None:
        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.discovery_url = reverse(
            "profiles:discovery",
        )

        self.password = (
            "Strong-Discovery-Test-Password-2026!"
        )

        self.user = User.objects.create_user(
            email="discovery-owner@example.com",
            password=self.password,
            is_email_verified=True,
        )
        Subscription.objects.create(
            user=self.user,
            plan=SubscriptionPlan.PLUS,
        )

        self.own_profile = Profile.objects.create(
            user=self.user,
            display_name="Profil personnel",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil du propriétaire.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        self.preferences = SearchPreferences.objects.create(
            user=self.user,
            minimum_age=25,
            maximum_age=40,
            preferred_genders=[
                "woman",
            ],
            preferred_cities=[
                "libreville",
            ],
            preferred_dating_intents=[
                "serious_relationship",
            ],
            maximum_distance_km=50,
            only_verified_profiles=True,
        )

    def tearDown(self) -> None:
        cache.clear()

    def authenticate(self) -> None:
        """
        Connecte le client de test avec une session Django.
        """

        self.client.force_login(
            self.user,
        )

    def create_candidate(
        self,
        *,
        email: str,
        display_name: str,
        age: int = 30,
        gender: str = "woman",
        city: str = "libreville",
        dating_intent: str = "serious_relationship",
        is_discoverable: bool = True,
        is_email_verified: bool = True,
        is_active: bool = True,
        is_suspended: bool = False,
    ) -> Profile:
        """
        Crée rapidement un profil candidat.

        Cette méthode évite de répéter la création complète
        du compte et du profil dans chaque test.
        """

        candidate_user = User.objects.create_user(
            email=email,
            password=self.password,
            is_email_verified=is_email_verified,
            is_active=is_active,
            is_suspended=is_suspended,
        )

        return Profile.objects.create(
            user=candidate_user,
            display_name=display_name,
            birth_date=years_ago(age),
            gender=gender,
            city=city,
            biography="Biographie du candidat.",
            dating_intent=dating_intent,
            is_discoverable=is_discoverable,
        )

    def get_result_ids(
        self,
        response,
    ) -> set[str]:
        """
        Extrait les UUID présents dans la page paginée.
        """

        return {
            str(item["id"])
            for item in response.data["results"]
        }

    def test_anonymous_user_cannot_access_discovery(
        self,
    ) -> None:
        response = self.client.get(
            self.discovery_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_matching_profile_is_returned(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="matching@example.com",
            display_name="Profil compatible",
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_current_user_is_excluded(
        self,
    ) -> None:
        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(self.own_profile.id),
            self.get_result_ids(response),
        )

    def test_non_discoverable_profile_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="private@example.com",
            display_name="Profil privé",
            is_discoverable=False,
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_unverified_profile_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="unverified@example.com",
            display_name="Profil non vérifié",
            is_email_verified=False,
            is_discoverable=False,
        )

        # Le modèle interdit normalement de rendre visible
        # un compte non vérifié.
        #
        # Nous forçons ici l'état directement en base pour tester
        # la défense supplémentaire du QuerySet de découverte.
        Profile.objects.filter(
            id=candidate.id,
        ).update(
            is_discoverable=True,
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_suspended_account_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="suspended@example.com",
            display_name="Profil suspendu",
            is_suspended=True,
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_inactive_account_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="inactive@example.com",
            display_name="Profil inactif",
            is_active=False,
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_profile_younger_than_minimum_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="young@example.com",
            display_name="Profil trop jeune",
            age=24,
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_profile_older_than_maximum_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="older@example.com",
            display_name="Profil trop âgé",
            age=41,
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_non_preferred_gender_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="gender@example.com",
            display_name="Genre non recherché",
            gender="man",
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_non_preferred_city_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="city@example.com",
            display_name="Ville non recherchée",
            city="port_gentil",
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_non_preferred_intent_is_excluded(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="intent@example.com",
            display_name="Intention incompatible",
            dating_intent="friendship",
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_private_fields_are_not_exposed(
        self,
    ) -> None:
        candidate = self.create_candidate(
            email="privacy@example.com",
            display_name="Profil confidentiel",
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        result = next(
            item
            for item in response.data["results"]
            if str(item["id"]) == str(candidate.id)
        )

        self.assertNotIn(
            "email",
            result,
        )

        self.assertNotIn(
            "birth_date",
            result,
        )

        self.assertNotIn(
            "user",
            result,
        )

        self.assertNotIn(
            "user_id",
            result,
        )

        self.assertNotIn(
            "is_suspended",
            result,
        )

        self.assertIn(
            "age",
            result,
        )

    def test_empty_choice_lists_disable_optional_filters(
        self,
    ) -> None:
        self.preferences.preferred_genders = []
        self.preferences.preferred_cities = []
        self.preferences.preferred_dating_intents = []

        self.preferences.save(
            update_fields=[
                "preferred_genders",
                "preferred_cities",
                "preferred_dating_intents",
                "updated_at",
            ]
        )

        candidate = self.create_candidate(
            email="unfiltered@example.com",
            display_name="Profil accepté sans filtre",
            gender="non_binary",
            city="oyem",
            dating_intent="friendship",
        )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertIn(
            str(candidate.id),
            self.get_result_ids(response),
        )

    def test_discovery_is_paginated(
        self,
    ) -> None:
        for index in range(25):
            self.create_candidate(
                email=f"page-{index}@example.com",
                display_name=f"Profil {index}",
            )

        self.authenticate()

        response = self.client.get(
            self.discovery_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            25,
        )

        self.assertEqual(
            len(response.data["results"]),
            20,
        )

        self.assertIsNotNone(
            response.data["next"],
        )

    def test_active_prestige_profile_is_ranked_before_newer_free_profile(
        self,
    ) -> None:
        prestige_profile = self.create_candidate(
            email="prestige-priority@example.com",
            display_name="Profil Prestige",
        )
        Subscription.objects.create(
            user=prestige_profile.user,
            plan=SubscriptionPlan.PRESTIGE,
            status=SubscriptionStatus.ACTIVE,
        )

        free_profile = self.create_candidate(
            email="newer-free@example.com",
            display_name="Profil gratuit plus récent",
        )

        self.authenticate()
        response = self.client.get(self.discovery_url)
        # Ici l'ordre est précisément ce que nous testons. Nous utilisons
        # donc une liste au lieu du helper historique qui retourne un set
        # pour les tests ne vérifiant que la présence.
        result_ids = [
            str(item["id"])
            for item in response.data["results"]
        ]

        self.assertLess(
            result_ids.index(str(prestige_profile.id)),
            result_ids.index(str(free_profile.id)),
        )

    def test_page_size_cannot_exceed_fifty(
        self,
    ) -> None:
        for index in range(55):
            self.create_candidate(
                email=f"limit-{index}@example.com",
                display_name=f"Limite {index}",
            )

        self.authenticate()

        response = self.client.get(
            f"{self.discovery_url}?page_size=1000"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            50,
        )
