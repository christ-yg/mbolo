from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.interactions.models import Match
from apps.profiles.models import Profile

from .models import Conversation, Message
from .services import (
    get_or_create_conversation,
    send_message,
)


User = get_user_model()


class MessagingServiceTests(TestCase):
    """
    Tests principaux de sécurité de la messagerie.
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
