"""
Tests de sécurité de la messagerie privée Mbolo.
"""

from datetime import date
from io import BytesIO
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from apps.interactions.models import Match
from apps.profiles.models import Profile
from apps.subscriptions.models import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)

from .models import Conversation, ConversationPreference, Message
from .serializers import MessageSerializer
from .services import (
    get_or_create_conversation,
    get_total_unread_count,
    mark_conversation_as_read,
    send_message,
    set_message_reaction,
    delete_message_for_everyone,
    edit_message,
    report_message,
    update_conversation_preferences,
)
from .typing import (
    get_other_typing_status,
    set_typing_status,
)


User = get_user_model()


def message_image_file() -> SimpleUploadedFile:
    buffer = BytesIO()
    image = Image.new("RGB", (640, 640), (125, 45, 92))
    image.save(buffer, format="JPEG")
    image.close()
    return SimpleUploadedFile(
        "client-name.jpg",
        buffer.getvalue(),
        content_type="image/jpeg",
    )


class MessagingServiceTests(TestCase):
    """
    Tests principaux de sécurité et de lecture.
    """

    def create_user_with_profile(
        self,
        *,
        email: str,
        display_name: str,
    ):
        user = User.objects.create_user(
            email=email,
            password="StrongPassword123!",
        )

        user.is_email_verified = True
        user.save(
            update_fields=[
                "is_email_verified",
            ]
        )

        profile = Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=date(1995, 1, 1),
            gender="man",
            city="libreville",
            biography="Profil de test sécurisé.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        return user, profile

    def create_active_match(
        self,
        *,
        profile_one: Profile,
        profile_two: Profile,
    ) -> Match:
        first, second = sorted(
            (
                profile_one,
                profile_two,
            ),
            key=lambda profile: str(profile.id),
        )

        return Match.objects.create(
            profile_one=first,
            profile_two=second,
            is_active=True,
        )

    def setUp(self):
        self.user_one, self.profile_one = (
            self.create_user_with_profile(
                email="one@example.com",
                display_name="Utilisateur un",
            )
        )

        self.user_two, self.profile_two = (
            self.create_user_with_profile(
                email="two@example.com",
                display_name="Utilisateur deux",
            )
        )

        self.outsider, self.outsider_profile = (
            self.create_user_with_profile(
                email="outsider@example.com",
                display_name="Utilisateur extérieur",
            )
        )

        self.match = self.create_active_match(
            profile_one=self.profile_one,
            profile_two=self.profile_two,
        )

    def test_participant_can_create_conversation(self):
        result = get_or_create_conversation(
            actor=self.user_one,
            match_id=self.match.id,
        )

        self.assertTrue(result.created)
        self.assertEqual(
            result.conversation.match,
            self.match,
        )

    def test_same_match_returns_existing_conversation(self):
        first_result = get_or_create_conversation(
            actor=self.user_one,
            match_id=self.match.id,
        )

        second_result = get_or_create_conversation(
            actor=self.user_two,
            match_id=self.match.id,
        )

        self.assertTrue(first_result.created)
        self.assertFalse(second_result.created)
        self.assertEqual(
            first_result.conversation.id,
            second_result.conversation.id,
        )

    def test_outsider_cannot_create_conversation(self):
        with self.assertRaises(ValidationError):
            get_or_create_conversation(
                actor=self.outsider,
                match_id=self.match.id,
            )

    def test_participant_can_send_message(self):
        result = get_or_create_conversation(
            actor=self.user_one,
            match_id=self.match.id,
        )

        message = send_message(
            actor=self.user_one,
            conversation_id=result.conversation.id,
            body="Bonjour.",
        )

        self.assertEqual(
            message.sender,
            self.user_one,
        )
        self.assertEqual(
            message.body,
            "Bonjour.",
        )
        self.assertIsNone(message.read_at)
        self.assertFalse(message.is_read)

    @override_settings(MEDIA_ROOT="/tmp/mbolo-test-media")
    def test_participant_can_send_sanitized_image_message(self):
        conversation = Conversation.objects.create(match=self.match)

        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="",
            image=message_image_file(),
        )

        self.assertEqual(message.body, "")
        self.assertTrue(message.image.name.endswith(".webp"))
        self.assertNotIn("client-name", message.image.name)

    def test_free_sender_cannot_receive_read_receipt(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Message gratuit.",
        )
        Message.objects.filter(pk=message.pk).update(read_at=timezone.now())
        message.refresh_from_db()

        data = MessageSerializer(
            message,
            context={"request": SimpleNamespace(user=self.user_one)},
        ).data

        self.assertFalse(data["read_receipts_available"])
        self.assertFalse(data["is_read"])
        self.assertIsNone(data["read_at"])

    def test_plus_sender_receives_read_receipt(self):
        Subscription.objects.create(
            user=self.user_one,
            plan=SubscriptionPlan.PLUS,
            status=SubscriptionStatus.ACTIVE,
        )
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Message Premium.",
        )
        Message.objects.filter(pk=message.pk).update(read_at=timezone.now())
        message.refresh_from_db()

        data = MessageSerializer(
            message,
            context={"request": SimpleNamespace(user=self.user_one)},
        ).data

        self.assertTrue(data["read_receipts_available"])
        self.assertTrue(data["is_read"])
        self.assertIsNotNone(data["read_at"])

    def test_outsider_cannot_send_message(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        with self.assertRaises(ValidationError):
            send_message(
                actor=self.outsider,
                conversation_id=conversation.id,
                body="Message interdit.",
            )

    def test_empty_message_is_rejected(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        with self.assertRaises(ValidationError):
            send_message(
                actor=self.user_one,
                conversation_id=conversation.id,
                body="   ",
            )

    def test_participant_can_add_replace_and_remove_reaction(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Bonjour.",
        )

        set_message_reaction(
            actor=self.user_two,
            conversation_id=conversation.id,
            message_id=message.id,
            emoji="❤️",
        )
        self.assertEqual(message.reactions.get().emoji, "❤️")

        set_message_reaction(
            actor=self.user_two,
            conversation_id=conversation.id,
            message_id=message.id,
            emoji="🔥",
        )
        self.assertEqual(message.reactions.get().emoji, "🔥")

        set_message_reaction(
            actor=self.user_two,
            conversation_id=conversation.id,
            message_id=message.id,
            emoji="",
        )
        self.assertFalse(message.reactions.exists())

    def test_participant_can_reply_inside_same_conversation(self):
        conversation = Conversation.objects.create(match=self.match)
        original = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Premier message.",
        )
        reply = send_message(
            actor=self.user_two,
            conversation_id=conversation.id,
            body="Réponse ciblée.",
            reply_to_id=original.id,
        )

        self.assertEqual(reply.reply_to_id, original.id)

    def test_sender_can_delete_message_for_everyone(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Contenu à supprimer.",
        )
        set_message_reaction(
            actor=self.user_two,
            conversation_id=conversation.id,
            message_id=message.id,
            emoji="❤️",
        )

        deleted = delete_message_for_everyone(
            actor=self.user_one,
            conversation_id=conversation.id,
            message_id=message.id,
        )

        self.assertIsNotNone(deleted.deleted_at)
        self.assertEqual(deleted.body, "")
        self.assertFalse(deleted.reactions.exists())

    def test_recipient_cannot_delete_sender_message(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Message protégé.",
        )

        with self.assertRaises(ValidationError):
            delete_message_for_everyone(
                actor=self.user_two,
                conversation_id=conversation.id,
                message_id=message.id,
            )

    def test_sender_can_edit_recent_message(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Ancien texte.",
        )

        edited = edit_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            message_id=message.id,
            body="  Nouveau texte.  ",
        )

        self.assertEqual(edited.body, "Nouveau texte.")
        self.assertIsNotNone(edited.edited_at)

    def test_recipient_cannot_edit_sender_message(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Texte protégé.",
        )

        with self.assertRaises(ValidationError):
            edit_message(
                actor=self.user_two,
                conversation_id=conversation.id,
                message_id=message.id,
                body="Tentative interdite.",
            )

    def test_recipient_can_report_message_with_server_evidence(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Contenu abusif à conserver.",
        )

        report = report_message(
            actor=self.user_two,
            conversation_id=conversation.id,
            message_id=message.id,
            reason="harassment",
            description="Ce message me met mal à l'aise.",
        )

        self.assertEqual(report.reported_user_id, self.user_one.id)
        self.assertIn(str(message.id), report.description)
        self.assertIn("Contenu abusif à conserver.", report.description)

    def test_sender_cannot_report_own_message(self):
        conversation = Conversation.objects.create(match=self.match)
        message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Mon message.",
        )

        with self.assertRaises(ValidationError):
            report_message(
                actor=self.user_one,
                conversation_id=conversation.id,
                message_id=message.id,
                reason="spam",
            )

    def test_participant_can_pin_and_mute_conversation_privately(self):
        conversation = Conversation.objects.create(match=self.match)

        update_conversation_preferences(
            actor=self.user_one,
            conversation_id=conversation.id,
            pinned=True,
            muted=True,
        )

        preference = ConversationPreference.objects.get(
            conversation=conversation,
            user=self.user_one,
        )
        self.assertTrue(preference.pinned)
        self.assertTrue(preference.muted)
        self.assertFalse(
            ConversationPreference.objects.filter(
                conversation=conversation,
                user=self.user_two,
            ).exists()
        )

    def test_reply_from_another_conversation_is_rejected(self):
        third_user, third_profile = self.create_user_with_profile(
            email="third@example.com",
            display_name="Troisième membre",
        )
        other_match = self.create_active_match(
            profile_one=self.profile_one,
            profile_two=third_profile,
        )
        other_conversation = Conversation.objects.create(match=other_match)
        foreign_message = send_message(
            actor=third_user,
            conversation_id=other_conversation.id,
            body="Message étranger.",
        )
        conversation = Conversation.objects.create(match=self.match)

        with self.assertRaises(ValidationError):
            send_message(
                actor=self.user_one,
                conversation_id=conversation.id,
                body="Réponse interdite.",
                reply_to_id=foreign_message.id,
            )

    def test_message_sender_must_belong_to_conversation(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        message = Message(
            conversation=conversation,
            sender=self.outsider,
            body="Message interdit.",
        )

        with self.assertRaises(ValidationError):
            message.save()

    def test_inactive_match_blocks_messages(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        self.match.is_active = False
        self.match.save(
            update_fields=[
                "is_active",
            ]
        )

        with self.assertRaises(ValidationError):
            send_message(
                actor=self.user_one,
                conversation_id=conversation.id,
                body="Message après désactivation.",
            )

    def test_received_message_is_counted_as_unread(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Message pour utilisateur deux.",
        )

        self.assertEqual(
            conversation.unread_count_for_user(
                self.user_one
            ),
            0,
        )

        self.assertEqual(
            conversation.unread_count_for_user(
                self.user_two
            ),
            1,
        )

        self.assertEqual(
            get_total_unread_count(
                actor=self.user_two
            ),
            1,
        )

    def test_mark_conversation_as_read_marks_received_messages(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        received_message = send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Message reçu.",
        )

        own_message = send_message(
            actor=self.user_two,
            conversation_id=conversation.id,
            body="Ma réponse.",
        )

        result = mark_conversation_as_read(
            actor=self.user_two,
            conversation_id=conversation.id,
        )

        received_message.refresh_from_db()
        own_message.refresh_from_db()

        self.assertEqual(result.marked_count, 1)
        self.assertIsNotNone(
            received_message.read_at
        )

        self.assertIsNone(
            own_message.read_at
        )

        self.assertEqual(
            conversation.unread_count_for_user(
                self.user_two
            ),
            0,
        )

    def test_mark_conversation_as_read_is_idempotent(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Message reçu.",
        )

        first_result = mark_conversation_as_read(
            actor=self.user_two,
            conversation_id=conversation.id,
        )

        second_result = mark_conversation_as_read(
            actor=self.user_two,
            conversation_id=conversation.id,
        )

        self.assertEqual(
            first_result.marked_count,
            1,
        )

        self.assertEqual(
            second_result.marked_count,
            0,
        )

    def test_outsider_cannot_mark_conversation_as_read(self):
        conversation = Conversation.objects.create(
            match=self.match,
        )

        send_message(
            actor=self.user_one,
            conversation_id=conversation.id,
            body="Message privé.",
        )

        with self.assertRaises(ValidationError):
            mark_conversation_as_read(
                actor=self.outsider,
                conversation_id=conversation.id,
            )


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mbolo-typing-tests",
        }
    }
)
class TypingIndicatorTests(MessagingServiceTests):
    """Tests de sécurité et d'expiration logique de la saisie."""

    def test_participant_can_publish_typing_status(self):
        conversation = Conversation.objects.create(match=self.match)
        result = set_typing_status(
            actor=self.user_one,
            conversation_id=conversation.id,
            is_typing=True,
        )
        self.assertTrue(result["is_typing"])
        other = get_other_typing_status(
            actor=self.user_two,
            conversation_id=conversation.id,
        )
        self.assertTrue(other["other_is_typing"])

    def test_participant_can_stop_typing(self):
        conversation = Conversation.objects.create(match=self.match)
        set_typing_status(
            actor=self.user_one, conversation_id=conversation.id, is_typing=True
        )
        set_typing_status(
            actor=self.user_one, conversation_id=conversation.id, is_typing=False
        )
        other = get_other_typing_status(
            actor=self.user_two, conversation_id=conversation.id
        )
        self.assertFalse(other["other_is_typing"])

    def test_outsider_cannot_publish_or_read_typing_status(self):
        conversation = Conversation.objects.create(match=self.match)
        with self.assertRaises(ValidationError):
            set_typing_status(
                actor=self.outsider, conversation_id=conversation.id, is_typing=True
            )
        with self.assertRaises(ValidationError):
            get_other_typing_status(
                actor=self.outsider, conversation_id=conversation.id
            )
