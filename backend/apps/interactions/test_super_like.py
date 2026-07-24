from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.notifications.models import Notification
from apps.profiles.models import Profile
from apps.subscriptions.models import Subscription, SubscriptionPlan

from .models import Interaction


User = get_user_model()


class SuperLikeTests(APITestCase):
    """Contrôles métier et sécurité du Super Like Premium."""

    def setUp(self):
        self.actor = User.objects.create_user(
            email="super-like-actor@example.com",
            password="Strong-Super-Like-2026!",
            is_email_verified=True,
        )
        self.target_user = User.objects.create_user(
            email="super-like-target@example.com",
            password="Strong-Super-Like-Target-2026!",
            is_email_verified=True,
        )
        self.actor_profile = Profile.objects.create(
            user=self.actor,
            display_name="Acteur",
            birth_date=date(1994, 1, 1),
            gender="man",
            city="libreville",
            biography="Profil complet acteur.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )
        self.target_profile = Profile.objects.create(
            user=self.target_user,
            display_name="Cible",
            birth_date=date(1995, 1, 1),
            gender="woman",
            city="libreville",
            biography="Profil complet cible.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )
        self.create_url = reverse("interactions:interaction-create")
        self.state_url = reverse("interactions:super-like-state")
        self.client.force_authenticate(self.actor)

    def send_super_like(self):
        return self.client.post(
            self.create_url,
            {
                "target_profile_id": str(self.target_profile.id),
                "decision": "like",
                "is_super_like": True,
            },
            format="json",
        )

    def test_free_account_cannot_send_super_like(self):
        response = self.send_super_like()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Interaction.objects.exists())

    def test_plus_can_send_one_super_like_and_notification_is_distinct(self):
        Subscription.objects.create(user=self.actor, plan=SubscriptionPlan.PLUS)
        response = self.send_super_like()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["is_super_like"])
        interaction = Interaction.objects.get()
        self.assertTrue(interaction.is_super_like)
        notification = Notification.objects.get(recipient=self.target_user)
        self.assertEqual(notification.kind, Notification.Kind.SUPER_LIKE)
        self.assertNotIn(self.actor.email, notification.title)
        self.assertNotIn(self.actor.email, notification.body)

    def test_plus_quota_is_one_per_day(self):
        Subscription.objects.create(user=self.actor, plan=SubscriptionPlan.PLUS)
        self.assertEqual(self.send_super_like().status_code, 201)
        second_target = User.objects.create_user(
            email="second-super-like-target@example.com",
            password="Strong-Second-Target-2026!",
            is_email_verified=True,
        )
        second_profile = Profile.objects.create(
            user=second_target,
            display_name="Deuxième cible",
            birth_date=date(1993, 1, 1),
            gender="woman",
            city="libreville",
            biography="Deuxième profil complet.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )
        response = self.client.post(
            self.create_url,
            {
                "target_profile_id": str(second_profile.id),
                "decision": "like",
                "is_super_like": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_prestige_state_exposes_three_daily_super_likes(self):
        Subscription.objects.create(
            user=self.actor,
            plan=SubscriptionPlan.PRESTIGE,
        )
        response = self.client.get(self.state_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["daily_limit"], 3)
        self.assertEqual(response.json()["remaining_today"], 3)

    def test_super_like_cannot_be_combined_with_pass(self):
        Subscription.objects.create(user=self.actor, plan=SubscriptionPlan.PLUS)
        response = self.client.post(
            self.create_url,
            {
                "target_profile_id": str(self.target_profile.id),
                "decision": "pass",
                "is_super_like": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_super_like_still_creates_match_after_reciprocal_like(self):
        Subscription.objects.create(user=self.actor, plan=SubscriptionPlan.PLUS)
        Interaction.objects.create(
            actor=self.target_user,
            target_profile=self.actor_profile,
            decision="like",
        )
        response = self.send_super_like()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["matched"])
        self.assertTrue(response.json()["match_created"])
