from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountSession
from apps.accounts.session_registry import (
    hash_session_key,
    register_current_session,
)


User = get_user_model()


class ConnectedDeviceTests(APITestCase):
    password = "Mbolo-Appareils-Connectes-2026!"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="devices@example.com",
            password=self.password,
            is_email_verified=True,
        )
        self.client.force_login(self.user)

    def test_session_key_is_never_stored_in_plain_text(self) -> None:
        request = self.client.get(
            reverse("accounts:security-sessions"),
        ).wsgi_request

        register_current_session(
            request=request,
            user=self.user,
            device="Chrome · Windows",
            ip_fingerprint="abcdef123456",
        )

        registry = AccountSession.objects.get(user=self.user)

        self.assertNotEqual(
            registry.session_key_hash,
            request.session.session_key,
        )
        self.assertEqual(
            registry.session_key_hash,
            hash_session_key(request.session.session_key),
        )

    def test_member_only_receives_own_sessions(self) -> None:
        other_user = User.objects.create_user(
            email="other-devices@example.com",
            password=self.password,
        )

        AccountSession.objects.create(
            user=other_user,
            session_key_hash="a" * 64,
            device="Firefox · Linux",
        )

        response = self.client.get(
            reverse("accounts:security-sessions"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"], [])

    def test_individual_revoke_requires_password(self) -> None:
        store = SessionStore()
        store["_auth_user_id"] = str(self.user.pk)
        store["_auth_user_backend"] = (
            "django.contrib.auth.backends.ModelBackend"
        )
        store.save()

        registry = AccountSession.objects.create(
            user=self.user,
            session_key_hash=hash_session_key(store.session_key),
            device="Firefox · Linux",
        )

        response = self.client.post(
            reverse(
                "accounts:security-session-revoke",
                kwargs={"session_id": registry.id},
            ),
            {
                "current_password": "mauvais",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertTrue(
            AccountSession.objects.filter(id=registry.id).exists()
        )

    def test_member_can_revoke_selected_other_session(self) -> None:
        store = SessionStore()
        store["_auth_user_id"] = str(self.user.pk)
        store["_auth_user_backend"] = (
            "django.contrib.auth.backends.ModelBackend"
        )
        store.save()

        registry = AccountSession.objects.create(
            user=self.user,
            session_key_hash=hash_session_key(store.session_key),
            device="Firefox · Linux",
        )

        response = self.client.post(
            reverse(
                "accounts:security-session-revoke",
                kwargs={"session_id": registry.id},
            ),
            {
                "current_password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            AccountSession.objects.filter(id=registry.id).exists()
        )
