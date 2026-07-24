from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import LoginActivity
from apps.notifications.models import Notification


User = get_user_model()


class NewLoginAlertTests(APITestCase):
    """
    Vérifie les alertes de connexion sans dépendre d'un serveur e-mail réel.

    Les limites anti-bruteforce utilisent le cache Django. Une transaction de
    test nettoie la base de données, mais pas nécessairement ce cache. Nous le
    vidons donc avant et après chaque test afin que les scénarios restent
    indépendants, sans désactiver les protections dans l'application réelle.
    """

    password = "Mbolo-Alerte-Connexion-2026!"

    chrome_windows = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
    )

    firefox_linux = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
        "Gecko/20100101 Firefox/128.0"
    )

    def setUp(self) -> None:
        cache.clear()

        self.user = User.objects.create_user(
            email="login.alert.member@example.com",
            password=self.password,
            is_email_verified=True,
        )

    def tearDown(self) -> None:
        cache.clear()
        super().tearDown()

    def _login(
        self,
        *,
        user_agent: str,
        remote_addr: str,
    ):
        return self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_USER_AGENT=user_agent,
            REMOTE_ADDR=remote_addr,
        )

    def test_first_login_creates_baseline_without_alert(self) -> None:
        response = self._login(
            user_agent=self.chrome_windows,
            remote_addr="203.0.113.10",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            LoginActivity.objects.filter(user=self.user).count(),
            1,
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.user,
                kind=Notification.Kind.SECURITY,
                source_key__startswith="security-login:",
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_known_device_and_fingerprint_do_not_repeat_alert(self) -> None:
        first_response = self._login(
            user_agent=self.chrome_windows,
            remote_addr="203.0.113.10",
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        self.client.logout()

        second_response = self._login(
            user_agent=self.chrome_windows,
            remote_addr="203.0.113.10",
        )

        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.user,
                source_key__startswith="security-login:",
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 0)

    @patch(
        "apps.accounts.login_alerts.broadcast_notification_created"
    )
    def test_new_device_creates_notification_email_and_realtime_event(
        self,
        mocked_broadcast,
    ) -> None:
        """
        Le centre React écoute précisément ``security.notification``.
        Ce test protège le contrat temps réel contre toute régression.
        """

        first_response = self._login(
            user_agent=self.chrome_windows,
            remote_addr="203.0.113.10",
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        self.client.logout()

        second_response = self._login(
            user_agent=self.firefox_linux,
            remote_addr="198.51.100.25",
        )

        self.assertEqual(second_response.status_code, status.HTTP_200_OK)

        alert = Notification.objects.get(
            recipient=self.user,
            source_key__startswith="security-login:",
        )

        self.assertEqual(alert.kind, Notification.Kind.SECURITY)
        self.assertEqual(alert.title, "Nouvelle connexion détectée")
        self.assertEqual(alert.target_path, "/security")
        self.assertEqual(alert.metadata["device"], "Firefox · Linux")
        self.assertNotIn("198.51.100.25", str(alert.metadata))
        self.assertNotIn("198.51.100.25", alert.body)
        self.assertNotIn(" à ", alert.body)

        mocked_broadcast.assert_called_once_with(
            notification=alert,
            event_name="security.notification",
            extra_payload={
                "security_event": "unrecognized_login",
            },
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "Nouvelle connexion détectée",
            mail.outbox[0].subject,
        )
        self.assertIn("Firefox · Linux", mail.outbox[0].body)
        self.assertIn("UTC", mail.outbox[0].body)
        self.assertNotIn("198.51.100.25", mail.outbox[0].body)

    def test_new_network_on_same_device_creates_alert(self) -> None:
        first_response = self._login(
            user_agent=self.chrome_windows,
            remote_addr="203.0.113.10",
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        self.client.logout()

        second_response = self._login(
            user_agent=self.chrome_windows,
            remote_addr="198.51.100.99",
        )

        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                source_key__startswith="security-login:",
            ).count(),
            1,
        )

    @patch(
        "apps.accounts.login_alerts.send_mail",
        side_effect=RuntimeError("service indisponible"),
    )
    def test_email_failure_never_blocks_login(self, mocked_send_mail) -> None:
        first_response = self._login(
            user_agent=self.chrome_windows,
            remote_addr="203.0.113.10",
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        self.client.logout()

        response = self._login(
            user_agent=self.firefox_linux,
            remote_addr="198.51.100.25",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mocked_send_mail.called)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user,
                source_key__startswith="security-login:",
            ).exists()
        )

    def test_notification_is_idempotent_for_same_activity(self) -> None:
        from apps.accounts.login_alerts import notify_unrecognized_login

        activity = LoginActivity.objects.create(
            user=self.user,
            method="password",
            device="Firefox · Linux",
            ip_fingerprint="abcd1234efgh",
        )

        first = notify_unrecognized_login(
            user=self.user,
            activity=activity,
        )
        second = notify_unrecognized_login(
            user=self.user,
            activity=activity,
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                source_key=f"security-login:{activity.id}",
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 1)
