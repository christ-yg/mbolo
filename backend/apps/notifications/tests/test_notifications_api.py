
import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from ..models import Notification
from ..services import create_message_notification


class NotificationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="recipient@example.com",
            password="StrongPassword2026!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPassword2026!",
        )
        self.client.force_authenticate(self.user)

    def create_notification(self, *, recipient=None, source_key="test:1"):
        return Notification.objects.create(
            recipient=recipient or self.user,
            kind=Notification.Kind.SYSTEM,
            title="Notification de test",
            body="Contenu public de test",
            target_path="/safety",
            source_key=source_key,
        )

    def test_list_returns_only_current_user_notifications(self):
        mine = self.create_notification()
        self.create_notification(
            recipient=self.other_user,
            source_key="test:other",
        )

        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            str(mine.id),
        )

    def test_unread_count_is_scoped_to_current_user(self):
        self.create_notification()
        self.create_notification(
            recipient=self.other_user,
            source_key="test:other",
        )

        response = self.client.get(
            reverse("notifications:unread-count")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 1)

    def test_mark_read_updates_only_owned_notification(self):
        notification = self.create_notification()

        response = self.client.post(
            reverse(
                "notifications:read",
                kwargs={"notification_id": notification.id},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

    def test_marking_another_users_notification_returns_404(self):
        notification = self.create_notification(
            recipient=self.other_user,
            source_key="test:other",
        )

        response = self.client.post(
            reverse(
                "notifications:read",
                kwargs={"notification_id": notification.id},
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_mark_all_marks_every_owned_unread_notification(self):
        self.create_notification(source_key="test:1")
        self.create_notification(source_key="test:2")

        response = self.client.post(
            reverse("notifications:read-all"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["marked_count"], 2)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                read_at__isnull=True,
            ).count(),
            0,
        )

    def test_delete_cannot_delete_another_users_notification(self):
        notification = self.create_notification(
            recipient=self.other_user,
            source_key="test:other",
        )

        response = self.client.delete(
            reverse(
                "notifications:delete",
                kwargs={"notification_id": notification.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertTrue(
            Notification.objects.filter(id=notification.id).exists()
        )

    def test_message_notification_service_is_idempotent(self):
        message_id = uuid.uuid4()
        conversation_id = uuid.uuid4()

        first = create_message_notification(
            recipient=self.user,
            sender_display_name="Kevin",
            conversation_id=conversation_id,
            message_id=message_id,
            body_preview="Bonjour",
        )
        second = create_message_notification(
            recipient=self.user,
            sender_display_name="Kevin",
            conversation_id=conversation_id,
            message_id=message_id,
            body_preview="Bonjour",
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.notification.id, second.notification.id)
        self.assertEqual(
            Notification.objects.filter(recipient=self.user).count(),
            1,
        )
