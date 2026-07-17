from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


# Récupère le modèle utilisateur réellement configuré dans Django.
# Dans Mbolo, il s'agit de notre modèle personnalisé accounts.User.
User = get_user_model()


class SessionAuthenticationTests(TestCase):
    """
    Tests de sécurité de la connexion et de la déconnexion par session.

    Ces tests vérifient notamment :

    - l'obligation du jeton CSRF ;
    - la création d'une session après connexion ;
    - la rotation de l'identifiant de session ;
    - le refus des identifiants invalides ;
    - le refus des comptes suspendus ;
    - le refus des comptes inactifs ;
    - la destruction de la session lors de la déconnexion ;
    - l'isolation des compteurs Redis entre chaque test.
    """

    def setUp(self) -> None:
        """
        Prépare un environnement propre avant chaque test.

        Redis est un service externe à la base PostgreSQL de test.
        Django réinitialise sa base de test, mais ne vide pas
        automatiquement Redis.

        Sans cache.clear(), les tentatives de connexion d'un test
        pourraient augmenter les compteurs anti-bruteforce et bloquer
        les tests suivants avec une réponse HTTP 429.
        """

        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.login_url = reverse(
            "accounts:login",
        )

        self.logout_url = reverse(
            "accounts:logout",
        )

        self.me_url = reverse(
            "accounts:current-user",
        )

        # Mot de passe exclusivement réservé à la base temporaire de test.
        # Il ne doit jamais être réutilisé sur un vrai compte.
        self.password = "A-Strong-Session-Test-Password-2026!"

        self.user = User.objects.create_user(
            email="session-user@example.com",
            password=self.password,
            is_email_verified=True,
        )

    def tearDown(self) -> None:
        """
        Nettoie Redis après chaque test.

        Cette étape garantit qu'aucun compteur anti-bruteforce,
        aucune clé temporaire ou autre donnée de cache ne puisse
        influencer le test suivant.
        """

        cache.clear()

    def get_csrf_token(self) -> str:
        """
        Récupère un jeton CSRF valide auprès de l'API.

        APIClient conserve également le cookie CSRF envoyé
        par Django, comme le ferait un navigateur.
        """

        response = self.client.get(
            self.csrf_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "csrfToken",
            response.data,
        )

        return response.data["csrfToken"]

    def login_user(self):
        """
        Connecte l'utilisateur de test avec un jeton CSRF valide.

        Cette méthode centralise le processus de connexion afin
        d'éviter de répéter le même code dans plusieurs tests.
        """

        csrf_token = self.get_csrf_token()

        return self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_login_requires_csrf_token(self) -> None:
        """
        Une tentative de connexion sans jeton CSRF doit être refusée.
        """

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_valid_credentials_create_session(self) -> None:
        """
        Des identifiants valides doivent créer une session Django.
        """

        response = self.login_user()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "sessionid",
            self.client.cookies,
        )

        me_response = self.client.get(
            self.me_url,
        )

        self.assertEqual(
            me_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            me_response.data["email"],
            self.user.email,
        )

        self.assertEqual(
            str(me_response.data["id"]),
            str(self.user.id),
        )

    def test_invalid_credentials_return_generic_message(self) -> None:
        """
        Un mot de passe incorrect doit produire un message générique.

        La réponse ne doit pas indiquer si l'adresse existe,
        afin de limiter l'énumération des comptes.
        """

        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": "Incorrect-Password-2026!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        response_text = response.content.decode().lower()

        self.assertIn(
            "adresse e-mail ou mot de passe incorrect",
            response_text,
        )

        self.assertNotIn(
            "existe",
            response_text,
        )

        self.assertNotIn(
            "introuvable",
            response_text,
        )

        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_unknown_email_uses_same_generic_failure(self) -> None:
        """
        Une adresse inconnue doit produire la même erreur générique
        qu'un mot de passe incorrect.
        """

        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": "unknown@example.com",
                "password": "Incorrect-Password-2026!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "adresse e-mail ou mot de passe incorrect",
            response.content.decode().lower(),
        )

        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_suspended_user_cannot_login(self) -> None:
        """
        Un compte suspendu ne doit pas pouvoir ouvrir de session.
        """

        self.user.is_suspended = True

        self.user.save(
            update_fields=[
                "is_suspended",
            ]
        )

        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_inactive_user_cannot_login(self) -> None:
        """
        Un compte désactivé avec is_active=False doit être refusé.
        """

        self.user.is_active = False

        self.user.save(
            update_fields=[
                "is_active",
            ]
        )

        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_login_rotates_session_key(self) -> None:
        """
        La connexion doit changer l'identifiant de session.

        Cette rotation limite les attaques par fixation de session :
        un identifiant de session anonyme préexistant ne doit pas
        rester identique après l'authentification.
        """

        csrf_token = self.get_csrf_token()

        # Création volontaire d'une session anonyme.
        session = self.client.session
        session["anonymous_marker"] = "before-login"
        session.save()

        previous_session_key = session.session_key

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        current_session_key = self.client.session.session_key

        self.assertIsNotNone(
            previous_session_key,
        )

        self.assertIsNotNone(
            current_session_key,
        )

        self.assertNotEqual(
            previous_session_key,
            current_session_key,
        )

    def test_logout_requires_authenticated_session(self) -> None:
        """
        Un utilisateur anonyme ne doit pas pouvoir appeler
        l'endpoint de déconnexion comme s'il était connecté.
        """

        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.logout_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_logout_requires_csrf_token(self) -> None:
        """
        Une session authentifiée ne suffit pas pour la déconnexion :
        la requête POST doit aussi contenir un jeton CSRF valide.
        """

        login_response = self.login_user()

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        response = self.client.post(
            self.logout_url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_logout_destroys_session(self) -> None:
        """
        Après la déconnexion, l'ancien client ne doit plus pouvoir
        accéder à l'endpoint protégé /auth/me/.
        """

        login_response = self.login_user()

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        csrf_token = self.get_csrf_token()

        logout_response = self.client.post(
            self.logout_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        me_response = self.client.get(
            self.me_url,
        )

        self.assertEqual(
            me_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
