"""
Tests fonctionnels et de sécurité du module Safety.

Les scénarios couvrent :

- authentification obligatoire ;
- protection CSRF ;
- création d'un blocage ;
- interdiction de l'auto-blocage ;
- blocage idempotent ;
- désactivation automatique des matchs ;
- liste privée des blocages ;
- protection contre les IDOR ;
- suppression d'un blocage ;
- exclusion bidirectionnelle de la découverte ;
- interdiction bidirectionnelle des interactions ;
- minimisation des données exposées.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.interactions.models import Match
from apps.profiles.models import (
    Profile,
    SearchPreferences,
)

from .models import Block


User = get_user_model()


def years_ago(
    years: int,
) -> date:
    """
    Retourne une date correspondant à un âge précis.

    Le cas du 29 février est traité afin que les tests
    fonctionnent pendant les années non bissextiles.
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


class SafetyBlockEndpointTests(TestCase):
    """
    Tests des endpoints de blocage.
    """

    def setUp(self) -> None:
        """
        Prépare deux utilisateurs complets et découvrables.
        """

        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.block_list_url = reverse(
            "safety:block-list-create",
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.discovery_url = reverse(
            "profiles:discovery",
        )

        self.interaction_url = reverse(
            "interactions:interaction-create",
        )

        self.password = (
            "Strong-Safety-Test-Password-2026!"
        )

        self.first_user, self.first_profile = (
            self.create_eligible_user(
                email="first-safety@example.com",
                display_name="Premier utilisateur",
                gender="man",
            )
        )

        self.second_user, self.second_profile = (
            self.create_eligible_user(
                email="second-safety@example.com",
                display_name="Deuxième utilisateur",
                gender="woman",
            )
        )

        # Préférences permettant aux deux profils
        # d'apparaître dans la découverte.
        SearchPreferences.objects.create(
            user=self.first_user,
            minimum_age=18,
            maximum_age=50,
            preferred_genders=[],
            preferred_cities=[],
            preferred_dating_intents=[],
        )

        SearchPreferences.objects.create(
            user=self.second_user,
            minimum_age=18,
            maximum_age=50,
            preferred_genders=[],
            preferred_cities=[],
            preferred_dating_intents=[],
        )

    def tearDown(self) -> None:
        """
        Nettoie le cache Redis après chaque test.
        """

        cache.clear()

    def create_eligible_user(
        self,
        *,
        email: str,
        display_name: str,
        gender: str,
    ):
        """
        Crée un compte vérifié et un profil complet.
        """

        user = User.objects.create_user(
            email=email,
            password=self.password,
            is_email_verified=True,
            is_active=True,
            is_suspended=False,
        )

        profile = Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=years_ago(30),
            gender=gender,
            city="libreville",
            biography="Biographie de test.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        return user, profile

    def authenticate(
        self,
        user=None,
    ) -> str:
        """
        Authentifie le client et récupère un jeton CSRF.
        """

        authenticated_user = user or self.first_user

        self.client.force_login(
            authenticated_user,
        )

        response = self.client.get(
            self.csrf_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.data["csrfToken"]

    def create_block_request(
        self,
        *,
        blocked_user_id,
        csrf_token: str,
    ):
        """
        Envoie une requête POST de blocage.
        """

        return self.client.post(
            self.block_list_url,
            {
                "blocked_user_id": str(
                    blocked_user_id
                ),
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def create_canonical_match(
        self,
        *,
        first_profile: Profile,
        second_profile: Profile,
    ) -> Match:
        """
        Crée un match en respectant l'ordre canonique des UUID.
        """

        profiles = sorted(
            (
                first_profile,
                second_profile,
            ),
            key=lambda profile: str(profile.id),
        )

        return Match.objects.create(
            profile_one=profiles[0],
            profile_two=profiles[1],
            is_active=True,
        )

    def result_ids(
        self,
        response,
    ) -> set[str]:
        """
        Extrait les identifiants d'une réponse paginée.
        """

        return {
            str(item["id"])
            for item in response.data["results"]
        }

    def test_anonymous_user_cannot_create_block(
        self,
    ) -> None:
        """
        Une personne non authentifiée doit être refusée.
        """

        response = self.client.post(
            self.block_list_url,
            {
                "blocked_user_id": str(
                    self.second_user.id
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Block.objects.count(),
            0,
        )

    def test_create_block_requires_csrf(
        self,
    ) -> None:
        """
        Une session sans jeton CSRF ne suffit pas.
        """

        self.client.force_login(
            self.first_user,
        )

        response = self.client.post(
            self.block_list_url,
            {
                "blocked_user_id": str(
                    self.second_user.id
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Block.objects.count(),
            0,
        )

    def test_user_can_block_another_user(
        self,
    ) -> None:
        """
        Un blocage valide doit être créé.
        """

        csrf_token = self.authenticate()

        response = self.create_block_request(
            blocked_user_id=self.second_user.id,
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            response.data["created"],
        )

        self.assertEqual(
            Block.objects.count(),
            1,
        )

        block = Block.objects.get()

        self.assertEqual(
            block.blocker,
            self.first_user,
        )

        self.assertEqual(
            block.blocked_user,
            self.second_user,
        )

    def test_user_cannot_block_self(
        self,
    ) -> None:
        """
        L'auto-blocage doit être refusé.
        """

        csrf_token = self.authenticate()

        response = self.create_block_request(
            blocked_user_id=self.first_user.id,
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Block.objects.count(),
            0,
        )

    def test_repeated_block_is_idempotent(
        self,
    ) -> None:
        """
        Le même blocage envoyé deux fois ne doit pas créer deux lignes.
        """

        csrf_token = self.authenticate()

        first_response = self.create_block_request(
            blocked_user_id=self.second_user.id,
            csrf_token=csrf_token,
        )

        second_response = self.create_block_request(
            blocked_user_id=self.second_user.id,
            csrf_token=csrf_token,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            second_response.data["created"],
        )

        self.assertEqual(
            Block.objects.count(),
            1,
        )

    def test_block_deactivates_existing_match(
        self,
    ) -> None:
        """
        Le blocage doit désactiver immédiatement un match actif.
        """

        match = self.create_canonical_match(
            first_profile=self.first_profile,
            second_profile=self.second_profile,
        )

        csrf_token = self.authenticate()

        response = self.create_block_request(
            blocked_user_id=self.second_user.id,
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        match.refresh_from_db()

        self.assertFalse(
            match.is_active,
        )

        self.assertEqual(
            response.data["deactivated_matches"],
            1,
        )

    def test_user_sees_only_own_blocks(
        self,
    ) -> None:
        """
        La liste doit contenir uniquement les blocages créés
        par l'utilisateur connecté.
        """

        third_user, _third_profile = (
            self.create_eligible_user(
                email="third-safety@example.com",
                display_name="Troisième utilisateur",
                gender="woman",
            )
        )

        own_block = Block.objects.create(
            blocker=self.first_user,
            blocked_user=self.second_user,
        )

        foreign_block = Block.objects.create(
            blocker=self.second_user,
            blocked_user=third_user,
        )

        self.client.force_login(
            self.first_user,
        )

        response = self.client.get(
            self.block_list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = self.result_ids(
            response
        )

        self.assertIn(
            str(own_block.id),
            returned_ids,
        )

        self.assertNotIn(
            str(foreign_block.id),
            returned_ids,
        )

    def test_block_list_does_not_expose_private_data(
        self,
    ) -> None:
        """
        La liste ne doit pas exposer l'e-mail ou la date de naissance.
        """

        Block.objects.create(
            blocker=self.first_user,
            blocked_user=self.second_user,
        )

        self.client.force_login(
            self.first_user,
        )

        response = self.client.get(
            self.block_list_url,
        )

        result = response.data["results"][0]

        self.assertIn(
            "blocked_profile",
            result,
        )

        profile_data = result["blocked_profile"]

        self.assertNotIn(
            "email",
            profile_data,
        )

        self.assertNotIn(
            "birth_date",
            profile_data,
        )

        self.assertNotIn(
            "phone_number",
            profile_data,
        )

        self.assertNotIn(
            "user_id",
            profile_data,
        )

    def test_owner_can_delete_own_block(
        self,
    ) -> None:
        """
        Le propriétaire du blocage peut le supprimer.
        """

        block = Block.objects.create(
            blocker=self.first_user,
            blocked_user=self.second_user,
        )

        csrf_token = self.authenticate()

        delete_url = reverse(
            "safety:block-delete",
            kwargs={
                "block_id": block.id,
            },
        )

        response = self.client.delete(
            delete_url,
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Block.objects.filter(
                id=block.id,
            ).exists()
        )

    def test_user_cannot_delete_foreign_block(
        self,
    ) -> None:
        """
        Un utilisateur ne peut pas supprimer le blocage d'un autre.

        Ce test couvre le risque IDOR.
        """

        third_user, _third_profile = (
            self.create_eligible_user(
                email="foreign-block@example.com",
                display_name="Utilisateur étranger",
                gender="man",
            )
        )

        foreign_block = Block.objects.create(
            blocker=self.second_user,
            blocked_user=third_user,
        )

        csrf_token = self.authenticate()

        delete_url = reverse(
            "safety:block-delete",
            kwargs={
                "block_id": foreign_block.id,
            },
        )

        response = self.client.delete(
            delete_url,
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertTrue(
            Block.objects.filter(
                id=foreign_block.id,
            ).exists()
        )

    def test_blocker_no_longer_sees_blocked_user(
        self,
    ) -> None:
        """
        L'utilisateur qui bloque ne doit plus voir la cible
        dans sa découverte.
        """

        Block.objects.create(
            blocker=self.first_user,
            blocked_user=self.second_user,
        )

        self.client.force_login(
            self.first_user,
        )

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(self.second_profile.id),
            self.result_ids(response),
        )

    def test_blocked_user_no_longer_sees_blocker(
        self,
    ) -> None:
        """
        L'utilisateur bloqué ne doit plus voir le bloqueur.

        Le comportement est donc bidirectionnel.
        """

        Block.objects.create(
            blocker=self.first_user,
            blocked_user=self.second_user,
        )

        self.client.force_login(
            self.second_user,
        )

        response = self.client.get(
            self.discovery_url,
        )

        self.assertNotIn(
            str(self.first_profile.id),
            self.result_ids(response),
        )

    def test_blocker_cannot_like_blocked_user(
        self,
    ) -> None:
        """
        Le bloqueur ne peut plus interagir avec la cible.
        """

        Block.objects.create(
            blocker=self.first_user,
            blocked_user=self.second_user,
        )

        csrf_token = self.authenticate(
            self.first_user
        )

        response = self.client.post(
            self.interaction_url,
            {
                "target_profile_id": str(
                    self.second_profile.id
                ),
                "decision": "like",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_blocked_user_cannot_like_blocker(
        self,
    ) -> None:
        """
        L'utilisateur bloqué ne peut pas non plus liker le bloqueur.
        """

        Block.objects.create(
            blocker=self.first_user,
            blocked_user=self.second_user,
        )

        csrf_token = self.authenticate(
            self.second_user
        )

        response = self.client.post(
            self.interaction_url,
            {
                "target_profile_id": str(
                    self.first_profile.id
                ),
                "decision": "like",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
