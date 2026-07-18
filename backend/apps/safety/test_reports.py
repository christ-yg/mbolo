"""
Tests fonctionnels et de sécurité des signalements utilisateurs.

Ce fichier vérifie notamment :

- l'authentification obligatoire ;
- la protection CSRF ;
- la validation des motifs ;
- l'interdiction de l'auto-signalement ;
- la limitation anti-spam avec Redis ;
- la protection contre le mass assignment ;
- l'isolation horizontale des données ;
- la minimisation des informations exposées ;
- l'impossibilité pour un utilisateur ordinaire de contrôler
  le workflow interne de modération.
"""

from datetime import date
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.profiles.models import Profile

from .models import (
    Report,
    ReportReason,
    ReportStatus,
)


User = get_user_model()


def years_ago(years: int) -> date:
    """
    Retourne une date de naissance correspondant à un âge précis.

    Le cas du 29 février est géré afin que les tests fonctionnent
    également pendant les années non bissextiles.
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


class ReportEndpointTests(TestCase):
    """
    Tests des endpoints publics de signalement.

    Endpoint testé :

        GET  /api/v1/safety/reports/
        POST /api/v1/safety/reports/
    """

    def setUp(self) -> None:
        """
        Prépare un environnement propre avant chaque test.

        cache.clear() empêche les compteurs Redis d'un test précédent
        d'influencer la limitation du test courant.
        """

        cache.clear()

        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        self.report_url = reverse(
            "safety:report-list-create",
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.password = (
            "Strong-Report-Test-Password-2026!"
        )

        self.reporter, self.reporter_profile = (
            self.create_eligible_user(
                email="reporter@example.com",
                display_name="Utilisateur déclarant",
                gender="man",
            )
        )

        self.target, self.target_profile = (
            self.create_eligible_user(
                email="target-report@example.com",
                display_name="Utilisateur signalé",
                gender="woman",
            )
        )

    def tearDown(self) -> None:
        """
        Nettoie Redis après chaque test.

        Cette seconde protection garantit que les compteurs créés
        par cette classe n'affectent pas les autres suites de tests.
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
        Crée un utilisateur actif, vérifié et non suspendu.

        Un profil complet est également créé afin de vérifier
        la représentation publique de la personne signalée.
        """

        user = User.objects.create_user(
            email=email,
            password=self.password,
            is_active=True,
            is_suspended=False,
            is_email_verified=True,
        )

        profile = Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=years_ago(30),
            gender=gender,
            city="libreville",
            biography="Biographie utilisée pour les tests.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        return user, profile

    def authenticate(self, user=None) -> str:
        """
        Connecte le client Django et récupère un jeton CSRF valide.

        SessionAuthentication exige deux protections :

        - une session authentifiée ;
        - un jeton CSRF pour les requêtes d'écriture.
        """

        authenticated_user = user or self.reporter

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

    def post_report(
        self,
        *,
        csrf_token: str,
        reported_user_id=None,
        reason: str = ReportReason.HARASSMENT,
        description: str = "Comportement abusif observé.",
        extra_payload: dict | None = None,
    ):
        """
        Envoie une requête POST de signalement.

        extra_payload permet de tester les tentatives de mass assignment.
        """

        payload = {
            "reported_user_id": str(
                reported_user_id or self.target.id
            ),
            "reason": reason,
            "description": description,
        }

        if extra_payload:
            payload.update(
                extra_payload
            )

        return self.client.post(
            self.report_url,
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_anonymous_user_cannot_create_report(
        self,
    ) -> None:
        """
        Une personne non authentifiée ne peut pas signaler un compte.
        """

        response = self.client.post(
            self.report_url,
            {
                "reported_user_id": str(
                    self.target.id
                ),
                "reason": ReportReason.HARASSMENT,
                "description": "Description de test.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Report.objects.count(),
            0,
        )

    def test_report_creation_requires_csrf(
        self,
    ) -> None:
        """
        Une session authentifiée sans CSRF doit être refusée.
        """

        self.client.force_login(
            self.reporter,
        )

        response = self.client.post(
            self.report_url,
            {
                "reported_user_id": str(
                    self.target.id
                ),
                "reason": ReportReason.HARASSMENT,
                "description": "Description de test.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Report.objects.count(),
            0,
        )

    def test_user_can_create_valid_report(
        self,
    ) -> None:
        """
        Un signalement valide doit être enregistré avec le statut pending.
        """

        csrf_token = self.authenticate()

        response = self.post_report(
            csrf_token=csrf_token,
            reason=ReportReason.HARASSMENT,
            description="Messages insistants et agressifs.",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Report.objects.count(),
            1,
        )

        report = Report.objects.get()

        self.assertEqual(
            report.reporter,
            self.reporter,
        )

        self.assertEqual(
            report.reported_user,
            self.target,
        )

        self.assertEqual(
            report.reason,
            ReportReason.HARASSMENT,
        )

        self.assertEqual(
            report.status,
            ReportStatus.PENDING,
        )

        self.assertIsNone(
            report.reviewed_by,
        )

        self.assertEqual(
            report.moderator_note,
            "",
        )

        self.assertIsNone(
            report.resolved_at,
        )

        self.assertEqual(
            response.data["data"]["status"],
            ReportStatus.PENDING,
        )

    def test_user_cannot_report_self(
        self,
    ) -> None:
        """
        Un utilisateur ne peut pas créer un signalement contre lui-même.
        """

        csrf_token = self.authenticate()

        response = self.post_report(
            csrf_token=csrf_token,
            reported_user_id=self.reporter.id,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Report.objects.count(),
            0,
        )

    def test_invalid_reason_is_rejected(
        self,
    ) -> None:
        """
        Un motif absent de ReportReason doit être rejeté.
        """

        csrf_token = self.authenticate()

        response = self.post_report(
            csrf_token=csrf_token,
            reason="give_me_admin_access",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "reason",
            response.data,
        )

        self.assertEqual(
            Report.objects.count(),
            0,
        )

    def test_other_reason_requires_description(
        self,
    ) -> None:
        """
        Le motif générique other doit être accompagné d'une explication.
        """

        csrf_token = self.authenticate()

        response = self.post_report(
            csrf_token=csrf_token,
            reason=ReportReason.OTHER,
            description="",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "description",
            response.data,
        )

        self.assertEqual(
            Report.objects.count(),
            0,
        )

    def test_description_is_normalized(
        self,
    ) -> None:
        """
        Les espaces et retours à la ligne inutiles doivent être réduits.
        """

        csrf_token = self.authenticate()

        response = self.post_report(
            csrf_token=csrf_token,
            description=(
                "Messages     agressifs\n\n"
                "et      répétitifs."
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        report = Report.objects.get()

        self.assertEqual(
            report.description,
            "Messages agressifs et répétitifs.",
        )

    def test_client_cannot_control_moderation_fields(
        self,
    ) -> None:
        """
        Le frontend ne doit pas pouvoir imposer les champs internes.

        Cette vérification couvre le risque de mass assignment.
        """

        moderator, _moderator_profile = (
            self.create_eligible_user(
                email="fake-moderator@example.com",
                display_name="Faux modérateur",
                gender="man",
            )
        )

        csrf_token = self.authenticate()

        response = self.post_report(
            csrf_token=csrf_token,
            extra_payload={
                "reporter": str(self.target.id),
                "status": ReportStatus.RESOLVED,
                "reviewed_by": str(moderator.id),
                "moderator_note": (
                    "Note injectée par le client."
                ),
                "resolved_at": (
                    "2026-07-18T10:00:00Z"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        report = Report.objects.get()

        # Le déclarant réel vient uniquement de request.user.
        self.assertEqual(
            report.reporter,
            self.reporter,
        )

        # Les champs de modération sont imposés côté serveur.
        self.assertEqual(
            report.status,
            ReportStatus.PENDING,
        )

        self.assertIsNone(
            report.reviewed_by,
        )

        self.assertEqual(
            report.moderator_note,
            "",
        )

        self.assertIsNone(
            report.resolved_at,
        )

    def test_user_sees_only_own_reports(
        self,
    ) -> None:
        """
        Un utilisateur ne peut pas consulter les signalements d'un tiers.
        """

        third_user, _third_profile = (
            self.create_eligible_user(
                email="third-reporter@example.com",
                display_name="Troisième utilisateur",
                gender="man",
            )
        )

        own_report = Report.objects.create(
            reporter=self.reporter,
            reported_user=self.target,
            reason=ReportReason.SPAM,
            description="Signalement personnel.",
        )

        foreign_report = Report.objects.create(
            reporter=third_user,
            reported_user=self.target,
            reason=ReportReason.SCAM,
            description="Signalement créé par un tiers.",
        )

        self.client.force_login(
            self.reporter,
        )

        response = self.client.get(
            self.report_url,
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
            str(own_report.id),
            returned_ids,
        )

        self.assertNotIn(
            str(foreign_report.id),
            returned_ids,
        )

    def test_report_list_does_not_expose_internal_data(
        self,
    ) -> None:
        """
        La réponse publique ne doit pas exposer les données de modération.
        """

        Report.objects.create(
            reporter=self.reporter,
            reported_user=self.target,
            reason=ReportReason.FAKE_PROFILE,
            description="Suspicion de faux profil.",
        )

        self.client.force_login(
            self.reporter,
        )

        response = self.client.get(
            self.report_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        result = response.data["results"][0]

        # Champs internes absents.
        self.assertNotIn(
            "reporter",
            result,
        )

        self.assertNotIn(
            "reviewed_by",
            result,
        )

        self.assertNotIn(
            "moderator_note",
            result,
        )

        self.assertNotIn(
            "resolved_at",
            result,
        )

        # Données privées du profil absentes.
        profile_data = result["reported_profile"]

        self.assertNotIn(
            "email",
            profile_data,
        )

        self.assertNotIn(
            "phone_number",
            profile_data,
        )

        self.assertNotIn(
            "birth_date",
            profile_data,
        )

        self.assertNotIn(
            "user_id",
            profile_data,
        )

    def test_unknown_target_returns_generic_error(
        self,
    ) -> None:
        """
        Un UUID inexistant doit produire une erreur générique.

        Le système ne doit pas révéler de détails techniques.
        """

        csrf_token = self.authenticate()

        response = self.post_report(
            csrf_token=csrf_token,
            reported_user_id=uuid4(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Report.objects.count(),
            0,
        )

        response_text = str(
            response.data
        ).lower()

        self.assertNotIn(
            "traceback",
            response_text,
        )

        self.assertNotIn(
            "doesnotexist",
            response_text,
        )

        self.assertNotIn(
            "sql",
            response_text,
        )

    def test_sixth_report_is_rate_limited(
        self,
    ) -> None:
        """
        Les cinq premières créations sont acceptées.

        La sixième tentative du même utilisateur doit produire
        HTTP 429 Too Many Requests.
        """

        csrf_token = self.authenticate()

        for attempt_number in range(5):
            response = self.post_report(
                csrf_token=csrf_token,
                reason=ReportReason.SPAM,
                description=(
                    f"Signalement autorisé numéro "
                    f"{attempt_number + 1}."
                ),
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
            )

        blocked_response = self.post_report(
            csrf_token=csrf_token,
            reason=ReportReason.SPAM,
            description="Sixième tentative.",
        )

        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

        self.assertEqual(
            Report.objects.count(),
            5,
        )
