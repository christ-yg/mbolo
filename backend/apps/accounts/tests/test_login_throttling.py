"""
Tests de sécurité de la limitation des tentatives de connexion Mbolo.

Deux limites distinctes sont vérifiées :

1. Limitation par adresse e-mail
   - cinq tentatives sont autorisées ;
   - la sixième tentative est bloquée.

2. Limitation par adresse IP
   - dix tentatives sont autorisées ;
   - la onzième tentative est bloquée.

Chaque test utilise un espace de clés Redis unique afin d'éviter
les contaminations entre plusieurs tests ou plusieurs exécutions.
"""

from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.throttles import (
    LoginEmailThrottle,
    LoginIPThrottle,
)


User = get_user_model()


class LoginThrottlingTests(TestCase):
    """
    Vérifie les protections anti-force brute de l'API de connexion.

    Endpoint testé :

        POST /api/v1/auth/login/
    """

    def setUp(self) -> None:
        """
        Prépare un environnement Redis et HTTP isolé.

        Nous :

        - supprimons les anciens compteurs Redis ;
        - créons un namespace aléatoire propre au test ;
        - mémorisons les préfixes normaux des throttles ;
        - configurons le client avec contrôle CSRF ;
        - créons un compte utilisateur valide.
        """

        # Nettoyage défensif avant chaque test.
        cache.clear()

        # Namespace Redis unique.
        #
        # Exemple :
        #
        # login-test-9ff3...:ip
        # login-test-9ff3...:email
        self.redis_test_namespace = (
            f"login-test-{uuid4().hex}"
        )

        # Conservation des valeurs utilisées normalement
        # par l'application.
        self.original_ip_cache_prefix = (
            LoginIPThrottle.cache_prefix
        )

        self.original_email_cache_prefix = (
            LoginEmailThrottle.cache_prefix
        )

        # Préfixes temporaires propres au test courant.
        LoginIPThrottle.cache_prefix = (
            f"{self.redis_test_namespace}:ip"
        )

        LoginEmailThrottle.cache_prefix = (
            f"{self.redis_test_namespace}:email"
        )

        # Client API avec validation CSRF réelle.
        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.login_url = reverse(
            "accounts:login",
        )

        self.password = (
            "Strong-Throttle-Test-Password-2026!"
        )

        # Compte valide permettant également de tester
        # une connexion avec le bon mot de passe.
        self.user = User.objects.create_user(
            email="throttle-user@example.com",
            password=self.password,
            is_active=True,
            is_suspended=False,
            is_email_verified=True,
        )

    def tearDown(self) -> None:
        """
        Nettoie Redis et restaure les préfixes de production.

        Les attributs cache_prefix appartiennent aux classes.
        Ils doivent donc être restaurés afin de ne pas influencer
        les autres fichiers de tests.
        """

        cache.clear()

        LoginIPThrottle.cache_prefix = (
            self.original_ip_cache_prefix
        )

        LoginEmailThrottle.cache_prefix = (
            self.original_email_cache_prefix
        )

    def get_csrf_token(self) -> str:
        """
        Récupère un jeton CSRF valide.

        L'appel crée également le cookie CSRF dans le client de test.
        """

        response = self.client.get(
            self.csrf_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.data["csrfToken"]

    def post_invalid_login(
        self,
        email: str,
        *,
        remote_addr: str,
    ):
        """
        Envoie une connexion avec un mot de passe volontairement faux.

        Une tentative non encore limitée doit retourner HTTP 400,
        car les identifiants sont incorrects.

        Une tentative limitée doit retourner HTTP 429.
        """

        csrf_token = self.get_csrf_token()

        return self.client.post(
            self.login_url,
            {
                "email": email,
                "password": (
                    "Incorrect-Throttle-Test-Password-2026!"
                ),
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
            REMOTE_ADDR=remote_addr,
        )

    def test_different_emails_have_separate_counters(
        self,
    ) -> None:
        """
        Deux adresses e-mail doivent avoir des compteurs distincts.

        Nous utilisons aussi deux IP différentes pour que le compteur IP
        ne puisse pas masquer le comportement du compteur par e-mail.
        """

        first_email = "first-throttle@example.com"
        second_email = "second-throttle@example.com"

        # Quatre échecs sur la première adresse.
        for _ in range(4):
            response = self.post_invalid_login(
                first_email,
                remote_addr="192.0.2.20",
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        # La première tentative sur une autre adresse doit rester autorisée.
        response = self.post_invalid_login(
            second_email,
            remote_addr="192.0.2.21",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_email_is_throttled_after_five_attempts(
        self,
    ) -> None:
        """
        Le throttle par e-mail autorise cinq tentatives.

        La sixième requête visant le même e-mail doit être bloquée.
        """

        test_email = self.user.email
        test_ip = "192.0.2.30"

        # Tentatives 1 à 5 : identifiants invalides, mais pas encore limitées.
        for _ in range(5):
            response = self.post_invalid_login(
                test_email,
                remote_addr=test_ip,
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        # Tentative 6 : limite par e-mail atteinte.
        blocked_response = self.post_invalid_login(
            test_email,
            remote_addr=test_ip,
        )

        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_ip_is_throttled_across_multiple_emails(
        self,
    ) -> None:
        """
        Une adresse IP doit être limitée même si elle change d'e-mail.

        Politique actuelle :

        - dix tentatives sont autorisées pour une IP ;
        - la onzième tentative retourne HTTP 429.

        Chaque requête utilise un e-mail différent afin que le throttle
        par e-mail ne soit jamais atteint avant le throttle par IP.
        """

        shared_ip_address = "192.0.2.50"

        # Tentatives 1 à 10 :
        #
        # chaque adresse e-mail est différente ;
        # seule l'adresse IP reste identique.
        for attempt_number in range(10):
            response = self.post_invalid_login(
                email=(
                    f"target-{attempt_number}"
                    f"@example.com"
                ),
                remote_addr=shared_ip_address,
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        # Tentative 11 :
        #
        # le compteur IP est maintenant au maximum.
        blocked_response = self.post_invalid_login(
            email="final-target@example.com",
            remote_addr=shared_ip_address,
        )

        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_successful_login_is_also_rate_limited(
        self,
    ) -> None:
        """
        Un bon mot de passe ne contourne pas une limite déjà atteinte.

        Cette protection empêche un attaquant de continuer à essayer
        jusqu'à trouver le mot de passe correct.
        """

        test_ip = "192.0.2.10"

        # Remplit le compteur e-mail avec cinq mots de passe incorrects.
        for _ in range(5):
            response = self.post_invalid_login(
                self.user.email,
                remote_addr=test_ip,
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        # Cette fois, le mot de passe est correct.
        #
        # Le throttle doit toutefois intervenir avant la création
        # de la session.
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
            REMOTE_ADDR=test_ip,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
