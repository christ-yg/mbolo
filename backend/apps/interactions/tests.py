"""
Tests fonctionnels et de sécurité des interactions et des matchs.

Les tests couvrent notamment :

- authentification obligatoire ;
- protection CSRF ;
- interdiction de l'auto-like ;
- profil privé inaccessible ;
- compte suspendu inaccessible ;
- création d'un like ;
- création d'un pass ;
- modification d'une interaction existante ;
- création d'un match réciproque ;
- prévention des matchs en double ;
- désactivation d'un match après retrait du like ;
- isolation des listes de matchs ;
- minimisation des données ;
- protection contre le mass assignment.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.profiles.models import Profile

from .models import (
    Interaction,
    InteractionDecision,
    Match,
)


User = get_user_model()


def years_ago(years: int) -> date:
    """
    Retourne une date de naissance correspondant à un âge précis.

    Le cas du 29 février est traité pour éviter que les tests
    échouent pendant une année non bissextile.
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


class InteractionEndpointTests(TestCase):
    """
    Tests du endpoint POST /api/v1/interactions/.
    """

    def setUp(self) -> None:
        """
        Crée un utilisateur principal et un profil cible valide.
        """

        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.interaction_url = reverse(
            "interactions:interaction-create",
        )

        self.match_list_url = reverse(
            "interactions:match-list",
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.password = (
            "Strong-Interaction-Test-Password-2026!"
        )

        self.actor_user, self.actor_profile = (
            self.create_eligible_user(
                email="actor@example.com",
                display_name="Utilisateur acteur",
                gender="man",
            )
        )

        self.target_user, self.target_profile = (
            self.create_eligible_user(
                email="target@example.com",
                display_name="Profil cible",
                gender="woman",
            )
        )

    def tearDown(self) -> None:
        """
        Nettoie les données temporaires placées dans Redis.
        """

        cache.clear()

    def create_eligible_user(
        self,
        *,
        email: str,
        display_name: str,
        gender: str,
        is_email_verified: bool = True,
        is_active: bool = True,
        is_suspended: bool = False,
        is_discoverable: bool = True,
    ) -> tuple:
        """
        Crée un compte et un profil complet.

        Les profils complets permettent de tester uniquement
        la logique des interactions sans dépendre de champs manquants.
        """

        user = User.objects.create_user(
            email=email,
            password=self.password,
            is_email_verified=is_email_verified,
            is_active=is_active,
            is_suspended=is_suspended,
        )

        # Un profil non vérifié ne peut normalement pas être visible.
        # Nous créons donc d'abord le profil privé lorsque nécessaire.
        safe_discoverable_value = (
            is_discoverable
            and is_email_verified
        )

        profile = Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=years_ago(30),
            gender=gender,
            city="libreville",
            biography="Biographie utilisée pendant les tests.",
            dating_intent="serious_relationship",
            is_discoverable=safe_discoverable_value,
        )

        if (
            is_discoverable
            and not safe_discoverable_value
        ):
            # Mise à jour directe uniquement pour simuler une donnée
            # incohérente ou ancienne et tester la défense en profondeur.
            Profile.objects.filter(
                id=profile.id,
            ).update(
                is_discoverable=True,
            )

            profile.refresh_from_db()

        return user, profile

    def authenticate(
        self,
        user=None,
    ) -> str:
        """
        Authentifie un utilisateur et récupère un jeton CSRF.
        """

        authenticated_user = user or self.actor_user

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

    def post_interaction(
        self,
        *,
        target_profile_id,
        decision: str,
        csrf_token: str,
        extra_payload: dict | None = None,
    ):
        """
        Envoie une interaction protégée par CSRF.
        """

        payload = {
            "target_profile_id": str(
                target_profile_id
            ),
            "decision": decision,
        }

        if extra_payload:
            payload.update(
                extra_payload
            )

        return self.client.post(
            self.interaction_url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_anonymous_user_cannot_create_interaction(
        self,
    ) -> None:
        """
        Une personne non connectée doit être refusée.
        """

        response = self.client.post(
            self.interaction_url,
            {
                "target_profile_id": str(
                    self.target_profile.id
                ),
                "decision": "like",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Interaction.objects.count(),
            0,
        )

    def test_post_requires_csrf_token(self) -> None:
        """
        Une session authentifiée ne suffit pas sans CSRF.
        """

        self.client.force_login(
            self.actor_user,
        )

        response = self.client.post(
            self.interaction_url,
            {
                "target_profile_id": str(
                    self.target_profile.id
                ),
                "decision": "like",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Interaction.objects.count(),
            0,
        )

    def test_user_can_like_eligible_profile(
        self,
    ) -> None:
        """
        Un like valide doit créer une interaction.
        """

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Interaction.objects.count(),
            1,
        )

        interaction = Interaction.objects.get()

        self.assertEqual(
            interaction.actor,
            self.actor_user,
        )

        self.assertEqual(
            interaction.target_profile,
            self.target_profile,
        )

        self.assertEqual(
            interaction.decision,
            InteractionDecision.LIKE,
        )

        self.assertFalse(
            response.data["matched"],
        )

    def test_user_can_pass_eligible_profile(
        self,
    ) -> None:
        """
        Un pass doit être enregistré sans créer de match.
        """

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="pass",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Interaction.objects.count(),
            1,
        )

        self.assertEqual(
            Match.objects.count(),
            0,
        )

        self.assertFalse(
            response.data["matched"],
        )

    def test_invalid_decision_is_rejected(
        self,
    ) -> None:
        """
        Toute décision différente de like ou pass doit être refusée.
        """

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="super_like_admin",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "decision",
            response.data,
        )

        self.assertEqual(
            Interaction.objects.count(),
            0,
        )

    def test_user_cannot_interact_with_own_profile(
        self,
    ) -> None:
        """
        L'auto-like et l'auto-pass sont interdits.
        """

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.actor_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Interaction.objects.count(),
            0,
        )

    def test_private_target_profile_is_rejected(
        self,
    ) -> None:
        """
        Un profil non découvrable ne peut pas recevoir d'interaction.
        """

        self.target_profile.is_discoverable = False

        self.target_profile.save(
            update_fields=[
                "is_discoverable",
                "updated_at",
            ]
        )

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Interaction.objects.count(),
            0,
        )

    def test_suspended_target_is_rejected(
        self,
    ) -> None:
        """
        Un compte suspendu doit être invisible au service.
        """

        self.target_user.is_suspended = True

        self.target_user.save(
            update_fields=[
                "is_suspended",
            ]
        )

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Interaction.objects.count(),
            0,
        )

    def test_unverified_target_is_rejected(
        self,
    ) -> None:
        """
        Un compte non vérifié ne peut pas recevoir d'interaction.
        """

        self.target_user.is_email_verified = False

        self.target_user.save(
            update_fields=[
                "is_email_verified",
            ]
        )

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Interaction.objects.count(),
            0,
        )

    def test_existing_pass_can_be_changed_to_like(
        self,
    ) -> None:
        """
        Une interaction existante doit être modifiée,
        sans créer une deuxième ligne.
        """

        csrf_token = self.authenticate()

        first_response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="pass",
            csrf_token=csrf_token,
        )

        second_response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
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

        self.assertEqual(
            Interaction.objects.count(),
            1,
        )

        interaction = Interaction.objects.get()

        self.assertEqual(
            interaction.decision,
            InteractionDecision.LIKE,
        )

        self.assertFalse(
            second_response.data["interaction_created"],
        )

    def test_mutual_like_creates_match(
        self,
    ) -> None:
        """
        Deux likes réciproques doivent créer un match unique.
        """

        # La cible like d'abord le profil de l'acteur.
        Interaction.objects.create(
            actor=self.target_user,
            target_profile=self.actor_profile,
            decision=InteractionDecision.LIKE,
        )

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            response.data["matched"],
        )

        self.assertTrue(
            response.data["match_created"],
        )

        self.assertIsNotNone(
            response.data["match_id"],
        )

        self.assertEqual(
            Match.objects.count(),
            1,
        )

        match = Match.objects.get()

        self.assertTrue(
            match.includes_profile(
                self.actor_profile
            )
        )

        self.assertTrue(
            match.includes_profile(
                self.target_profile
            )
        )

    def test_repeated_like_does_not_duplicate_match(
        self,
    ) -> None:
        """
        Répéter un like ne doit pas créer un second match.
        """

        Interaction.objects.create(
            actor=self.target_user,
            target_profile=self.actor_profile,
            decision=InteractionDecision.LIKE,
        )

        csrf_token = self.authenticate()

        first_response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        second_response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
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

        self.assertEqual(
            Interaction.objects.filter(
                actor=self.actor_user,
                target_profile=self.target_profile,
            ).count(),
            1,
        )

        self.assertEqual(
            Match.objects.count(),
            1,
        )

        self.assertFalse(
            second_response.data["match_created"],
        )

    def test_pass_after_match_deactivates_match(
        self,
    ) -> None:
        """
        Retirer son like doit rendre le match inactif.
        """

        Interaction.objects.create(
            actor=self.target_user,
            target_profile=self.actor_profile,
            decision=InteractionDecision.LIKE,
        )

        csrf_token = self.authenticate()

        like_response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
        )

        self.assertTrue(
            like_response.data["matched"],
        )

        match = Match.objects.get()

        self.assertTrue(
            match.is_active,
        )

        pass_response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="pass",
            csrf_token=csrf_token,
        )

        self.assertEqual(
            pass_response.status_code,
            status.HTTP_200_OK,
        )

        match.refresh_from_db()

        self.assertFalse(
            match.is_active,
        )

        self.assertFalse(
            pass_response.data["matched"],
        )

    def test_client_cannot_choose_actor(
        self,
    ) -> None:
        """
        Le client ne doit jamais pouvoir imposer l'utilisateur acteur.

        Même si un champ actor ou user_id est envoyé, le backend
        doit utiliser exclusivement request.user.
        """

        attacker_user, _attacker_profile = (
            self.create_eligible_user(
                email="attacker@example.com",
                display_name="Autre utilisateur",
                gender="man",
            )
        )

        csrf_token = self.authenticate()

        response = self.post_interaction(
            target_profile_id=self.target_profile.id,
            decision="like",
            csrf_token=csrf_token,
            extra_payload={
                "actor": str(attacker_user.id),
                "user_id": str(attacker_user.id),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        interaction = Interaction.objects.get()

        self.assertEqual(
            interaction.actor,
            self.actor_user,
        )

        self.assertNotEqual(
            interaction.actor,
            attacker_user,
        )


class MatchListEndpointTests(TestCase):
    """
    Tests du endpoint GET /api/v1/matches/.
    """

    def setUp(self) -> None:
        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.match_list_url = reverse(
            "interactions:match-list",
        )

        self.password = (
            "Strong-Match-List-Password-2026!"
        )

        self.first_user = User.objects.create_user(
            email="first-match@example.com",
            password=self.password,
            is_email_verified=True,
        )

        self.second_user = User.objects.create_user(
            email="second-match@example.com",
            password=self.password,
            is_email_verified=True,
        )

        self.third_user = User.objects.create_user(
            email="third-match@example.com",
            password=self.password,
            is_email_verified=True,
        )

        self.first_profile = self.create_profile(
            self.first_user,
            "Premier profil",
            "man",
        )

        self.second_profile = self.create_profile(
            self.second_user,
            "Deuxième profil",
            "woman",
        )

        self.third_profile = self.create_profile(
            self.third_user,
            "Troisième profil",
            "woman",
        )

    def tearDown(self) -> None:
        cache.clear()

    def create_profile(
        self,
        user,
        display_name: str,
        gender: str,
    ) -> Profile:
        """
        Crée un profil complet et découvrable.
        """

        return Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=years_ago(30),
            gender=gender,
            city="libreville",
            biography="Profil de test.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

    def create_match(
        self,
        first_profile: Profile,
        second_profile: Profile,
        *,
        is_active: bool = True,
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
            is_active=is_active,
        )

    def test_anonymous_user_cannot_list_matches(
        self,
    ) -> None:
        """
        Les matchs sont privés et nécessitent une session.
        """

        response = self.client.get(
            self.match_list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_sees_only_own_active_matches(
        self,
    ) -> None:
        """
        Un utilisateur ne doit jamais voir les matchs des autres.
        """

        own_match = self.create_match(
            self.first_profile,
            self.second_profile,
        )

        foreign_match = self.create_match(
            self.second_profile,
            self.third_profile,
        )

        self.client.force_login(
            self.first_user,
        )

        response = self.client.get(
            self.match_list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            str(item["id"])
            for item in response.data["results"]
        }

        self.assertIn(
            str(own_match.id),
            returned_ids,
        )

        self.assertNotIn(
            str(foreign_match.id),
            returned_ids,
        )

    def test_inactive_match_is_not_returned(
        self,
    ) -> None:
        """
        Un match désactivé ne doit plus apparaître.
        """

        inactive_match = self.create_match(
            self.first_profile,
            self.second_profile,
            is_active=False,
        )

        self.client.force_login(
            self.first_user,
        )

        response = self.client.get(
            self.match_list_url,
        )

        returned_ids = {
            str(item["id"])
            for item in response.data["results"]
        }

        self.assertNotIn(
            str(inactive_match.id),
            returned_ids,
        )

    def test_match_response_does_not_expose_private_data(
        self,
    ) -> None:
        """
        La réponse ne doit contenir ni e-mail ni date de naissance.
        """

        self.create_match(
            self.first_profile,
            self.second_profile,
        )

        self.client.force_login(
            self.first_user,
        )

        response = self.client.get(
            self.match_list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        result = response.data["results"][0]

        self.assertIn(
            "other_profile",
            result,
        )

        other_profile = result["other_profile"]

        self.assertEqual(
            other_profile["display_name"],
            "Deuxième profil",
        )

        self.assertNotIn(
            "email",
            other_profile,
        )

        self.assertNotIn(
            "birth_date",
            other_profile,
        )

        self.assertNotIn(
            "user_id",
            other_profile,
        )

        self.assertNotIn(
            "phone_number",
            other_profile,
        )

        self.assertIn(
            "age",
            other_profile,
        )
