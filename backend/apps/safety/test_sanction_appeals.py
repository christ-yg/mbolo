from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import (
    ModerationSanction,
    ModerationSanctionType,
    Report,
    ReportReason,
    SanctionAppeal,
)


User = get_user_model()


class SanctionAppealApiTests(TestCase):
    """Protège les règles essentielles du formulaire public."""

    def setUp(self):
        self.password = "Strong-Appeal-Password-2026!"
        self.reporter = User.objects.create_user(
            email="appeal-reporter@example.com",
            password=self.password,
        )
        self.user = User.objects.create_user(
            email="appeal-user@example.com",
            password=self.password,
            is_suspended=True,
        )
        self.moderator = User.objects.create_superuser(
            email="appeal-moderator@example.com",
            password=self.password,
        )
        report = Report.objects.create(
            reporter=self.reporter,
            reported_user=self.user,
            reason=ReportReason.HARASSMENT,
            description="Signalement de test suffisamment détaillé.",
        )
        self.sanction = ModerationSanction.objects.create(
            report=report,
            user=self.user,
            moderator=self.moderator,
            sanction_type=ModerationSanctionType.PERMANENT_SUSPENSION,
        )
        self.client = APIClient(enforce_csrf_checks=True)
        self.url = reverse("safety:sanction-appeal-create")

    def _csrf(self):
        self.client.get("/api/v1/csrf/")
        return self.client.cookies["csrftoken"].value

    def test_valid_credentials_create_one_appeal(self):
        response = self.client.post(
            self.url,
            {
                "email": self.user.email,
                "password": self.password,
                "message": "Je souhaite expliquer la situation et demander une révision.",
            },
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SanctionAppeal.objects.count(), 1)

    def test_wrong_password_does_not_create_appeal(self):
        response = self.client.post(
            self.url,
            {
                "email": self.user.email,
                "password": "Wrong-Password!",
                "message": "Je souhaite expliquer la situation et demander une révision.",
            },
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf(),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(SanctionAppeal.objects.exists())

    def test_second_appeal_is_rejected(self):
        SanctionAppeal.objects.create(
            sanction=self.sanction,
            user=self.user,
            message="Première contestation suffisamment détaillée.",
        )
        response = self.client.post(
            self.url,
            {
                "email": self.user.email,
                "password": self.password,
                "message": "Deuxième contestation qui ne doit pas être enregistrée.",
            },
            format="json",
            HTTP_X_CSRFTOKEN=self._csrf(),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SanctionAppeal.objects.count(), 1)
