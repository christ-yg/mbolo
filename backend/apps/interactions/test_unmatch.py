
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.messaging.models import Conversation, Message
from apps.profiles.models import Profile

from .models import (
    Interaction,
    InteractionDecision,
    Match,
)


User = get_user_model()


def years_ago(years: int) -> date:
    today = date.today()

    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(
            year=today.year - years,
            month=2,
            day=28,
        )


class UnmatchApiTests(APITestCase):
    def setUp(self) -> None:
        self.actor = User.objects.create_user(
            email="unmatch-actor@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        self.actor_profile = Profile.objects.create(
            user=self.actor,
            display_name="Christ",
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography="Profil acteur.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        self.other = User.objects.create_user(
            email="unmatch-other@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        self.other_profile = Profile.objects.create(
            user=self.other,
            display_name="Kevin",
            birth_date=years_ago(29),
            gender="woman",
            city="moanda",
            biography="Profil cible.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        first, second = sorted(
            (self.actor_profile, self.other_profile),
            key=lambda profile: str(profile.id),
        )

        self.match = Match.objects.create(
            profile_one=first,
            profile_two=second,
            is_active=True,
        )

        self.conversation = Conversation.objects.create(
            match=self.match,
        )

        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.actor,
            body="Message conservé pour audit.",
        )

        Interaction.objects.create(
            actor=self.actor,
            target_profile=self.other_profile,
            decision=InteractionDecision.LIKE,
        )

        Interaction.objects.create(
            actor=self.other,
            target_profile=self.actor_profile,
            decision=InteractionDecision.LIKE,
        )

        self.client.force_authenticate(self.actor)

        self.url = reverse(
            "interactions:match-deactivate",
            kwargs={"match_id": self.match.id},
        )

    def test_participant_can_deactivate_match(self):
        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(response.data["deactivated"])

        self.match.refresh_from_db()
        self.assertFalse(self.match.is_active)

    def test_messages_and_conversation_are_preserved(self):
        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            Conversation.objects.filter(
                id=self.conversation.id,
            ).exists()
        )
        self.assertTrue(
            Message.objects.filter(
                id=self.message.id,
            ).exists()
        )

    def test_actor_interaction_is_removed_for_rediscovery(self):
        self.client.delete(self.url)

        self.assertFalse(
            Interaction.objects.filter(
                actor=self.actor,
                target_profile=self.other_profile,
            ).exists()
        )

        self.assertTrue(
            Interaction.objects.filter(
                actor=self.other,
                target_profile=self.actor_profile,
            ).exists()
        )

    def test_conversation_becomes_inaccessible(self):
        self.client.delete(self.url)

        response = self.client.get(
            reverse(
                "messaging:conversation-message-list-create",
                kwargs={
                    "conversation_id": self.conversation.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_non_participant_cannot_deactivate_match(self):
        outsider = User.objects.create_user(
            email="unmatch-outsider@example.com",
            password="StrongPassword2026!",
            is_email_verified=True,
        )
        Profile.objects.create(
            user=outsider,
            display_name="Amina",
            birth_date=years_ago(27),
            gender="woman",
            city="oyem",
            biography="Profil extérieur.",
            dating_intent="friendship",
            is_discoverable=True,
        )

        self.client.force_authenticate(outsider)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.match.refresh_from_db()
        self.assertTrue(self.match.is_active)
