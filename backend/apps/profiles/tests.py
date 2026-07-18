from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Profile


User = get_user_model()


def years_ago(
    years: int,
) -> date:
    """
    Retourne une date située exactement un certain nombre
    d'années avant aujourd'hui.

    Le cas particulier du 29 février est géré afin que les tests
    restent fonctionnels pendant les années non bissextiles.
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


class CurrentProfileEndpointTests(TestCase):
    """
    Tests fonctionnels et de sécurité du profil personnel.

    Les contrôles couvrent :

    - l'authentification obligatoire ;
    - la création automatique du profil ;
    - la modification partielle par PATCH ;
    - l'âge minimum de 18 ans ;
    - le rejet d'une date future ;
    - l'obligation de compléter le profil avant publication ;
    - la vérification obligatoire de l'e-mail ;
    - l'isolation entre les utilisateurs ;
    - l'impossibilité de modifier les champs techniques.
    """

    def setUp(self) -> None:
        """
        Prépare un environnement indépendant avant chaque test.
        """

        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.profile_url = reverse(
            "profiles:current-profile",
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.password = (
            "Strong-Profile-Test-Password-2026!"
        )

        self.user = User.objects.create_user(
            email="profile-user@example.com",
            password=self.password,
            is_email_verified=False,
        )

    def tearDown(self) -> None:
        """
        Nettoie Redis après chaque test.
        """

        cache.clear()

    def authenticate(
        self,
        user=None,
    ) -> str:
        """
        Authentifie le client et récupère un jeton CSRF valide.

        force_login crée une véritable session Django de test.
        """

        authenticated_user = user or self.user

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

    def valid_profile_payload(
        self,
    ) -> dict:
        """
        Retourne un profil complet appartenant à un adulte.
        """

        return {
            "display_name": "Christ YG",
            "birth_date": years_ago(25).isoformat(),
            "gender": "man",
            "city": "libreville",
            "biography": (
                "Passionné de technologie, de sport "
                "et de développement personnel."
            ),
            "dating_intent": "serious_relationship",
        }

    def patch_profile(
        self,
        payload: dict,
        csrf_token: str,
    ):
        """
        Envoie une modification partielle protégée par CSRF.
        """

        return self.client.patch(
            self.profile_url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_anonymous_user_cannot_access_profile(
        self,
    ) -> None:
        """
        Un utilisateur non connecté doit être refusé.
        """

        response = self.client.get(
            self.profile_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Profile.objects.count(),
            0,
        )

    def test_get_creates_profile_for_authenticated_user(
        self,
    ) -> None:
        """
        Le premier accès crée automatiquement le profil personnel.
        """

        self.authenticate()

        response = self.client.get(
            self.profile_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            Profile.objects.count(),
            1,
        )

        profile = Profile.objects.get(
            user=self.user,
        )

        self.assertEqual(
            str(response.data["id"]),
            str(profile.id),
        )

        self.assertEqual(
            response.data["display_name"],
            "",
        )

        self.assertFalse(
            response.data["is_complete"],
        )

        self.assertFalse(
            response.data["is_discoverable"],
        )

    def test_authenticated_user_can_update_own_profile(
        self,
    ) -> None:
        """
        Un utilisateur connecté peut compléter son propre profil.
        """

        csrf_token = self.authenticate()

        response = self.patch_profile(
            self.valid_profile_payload(),
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        profile = Profile.objects.get(
            user=self.user,
        )

        self.assertEqual(
            profile.display_name,
            "Christ YG",
        )

        self.assertEqual(
            profile.city,
            "libreville",
        )

        self.assertEqual(
            profile.gender,
            "man",
        )

        self.assertEqual(
            profile.dating_intent,
            "serious_relationship",
        )

        self.assertTrue(
            profile.is_complete,
        )

        self.assertGreaterEqual(
            profile.age,
            18,
        )

    def test_display_name_is_normalized(
        self,
    ) -> None:
        """
        Les espaces inutiles dans le nom public sont supprimés.
        """

        csrf_token = self.authenticate()

        response = self.patch_profile(
            {
                "display_name": (
                    "   Christ     YG   "
                ),
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["display_name"],
            "Christ YG",
        )

    def test_minor_birth_date_is_rejected(
        self,
    ) -> None:
        """
        Un utilisateur de moins de 18 ans doit être refusé.
        """

        csrf_token = self.authenticate()

        response = self.patch_profile(
            {
                "birth_date": (
                    years_ago(17).isoformat()
                ),
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "birth_date",
            response.data,
        )

        self.assertIn(
            "18",
            response.content.decode(),
        )

    def test_future_birth_date_is_rejected(
        self,
    ) -> None:
        """
        Une date de naissance située dans le futur doit être refusée.
        """

        csrf_token = self.authenticate()

        future_date = date(
            date.today().year + 1,
            1,
            1,
        )

        response = self.patch_profile(
            {
                "birth_date": (
                    future_date.isoformat()
                ),
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "birth_date",
            response.data,
        )

    def test_incomplete_profile_cannot_be_discoverable(
        self,
    ) -> None:
        """
        Un profil incomplet ne peut pas apparaître dans la découverte.
        """

        self.user.is_email_verified = True

        self.user.save(
            update_fields=[
                "is_email_verified",
            ]
        )

        csrf_token = self.authenticate()

        response = self.patch_profile(
            {
                "display_name": "Christ",
                "is_discoverable": True,
            },
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "is_discoverable",
            response.data,
        )

    def test_unverified_user_cannot_publish_profile(
        self,
    ) -> None:
        """
        Un profil complet reste privé tant que l'e-mail
        du propriétaire n'est pas vérifié.
        """

        csrf_token = self.authenticate()

        payload = {
            **self.valid_profile_payload(),
            "is_discoverable": True,
        }

        response = self.patch_profile(
            payload,
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "is_discoverable",
            response.data,
        )

        profile = Profile.objects.get(
            user=self.user,
        )

        self.assertFalse(
            profile.is_discoverable,
        )

    def test_verified_adult_with_complete_profile_can_publish(
        self,
    ) -> None:
        """
        Un adulte avec e-mail vérifié et profil complet
        peut activer la visibilité.
        """

        self.user.is_email_verified = True

        self.user.save(
            update_fields=[
                "is_email_verified",
            ]
        )

        csrf_token = self.authenticate()

        payload = {
            **self.valid_profile_payload(),
            "is_discoverable": True,
        }

        response = self.patch_profile(
            payload,
            csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data["is_discoverable"],
        )

        profile = Profile.objects.get(
            user=self.user,
        )

        self.assertTrue(
            profile.is_discoverable,
        )

    def test_each_user_receives_only_own_profile(
        self,
    ) -> None:
        """
        L'endpoint /profiles/me/ ne doit jamais exposer
        le profil d'un autre utilisateur.
        """

        first_profile = Profile.objects.create(
            user=self.user,
            display_name="Premier utilisateur",
        )

        second_user = User.objects.create_user(
            email="second-profile-user@example.com",
            password=self.password,
            is_email_verified=True,
        )

        second_profile = Profile.objects.create(
            user=second_user,
            display_name="Deuxième utilisateur",
        )

        self.client.logout()

        self.authenticate(
            user=second_user,
        )

        response = self.client.get(
            self.profile_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            str(response.data["id"]),
            str(second_profile.id),
        )

        self.assertNotEqual(
            str(response.data["id"]),
            str(first_profile.id),
        )

        self.assertEqual(
            response.data["display_name"],
            "Deuxième utilisateur",
        )

    def test_client_cannot_replace_profile_id(
        self,
    ) -> None:
        """
        Les champs techniques en lecture seule ne peuvent
        pas être modifiés par le client.
        """

        csrf_token = self.authenticate()

        original_response = self.client.get(
            self.profile_url,
        )

        original_id = str(
            original_response.data["id"]
        )

        response = self.patch_profile(
            {
                "id": (
                    "00000000-0000-0000-0000-000000000001"
                ),
                "created_at": "2000-01-01T00:00:00Z",
                "display_name": "Nom autorisé",
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

        self.assertEqual(
            response.data["display_name"],
            "Nom autorisé",
        )

    def test_patch_requires_csrf_token(
        self,
    ) -> None:
        """
        Une modification de profil sans CSRF doit être refusée.
        """

        self.client.force_login(
            self.user,
        )

        response = self.client.patch(
            self.profile_url,
            {
                "display_name": "Test CSRF",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
