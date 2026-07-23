from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .models import Profile
from .serializers import (
    DiscoveryProfileSerializer,
    ProfileSerializer,
)


User = get_user_model()


class ProfileInterestTests(TestCase):
    """
    Vérifie la validation et le calcul explicable de compatibilité.
    """

    def create_profile(
        self,
        *,
        email: str,
        name: str,
        interests: list[str],
    ) -> Profile:
        user = User.objects.create_user(
            email=email,
            password="Strong-Interest-Test-2026!",
            is_email_verified=True,
        )

        return Profile.objects.create(
            user=user,
            display_name=name,
            birth_date=date(1995, 1, 1),
            gender="man",
            city="libreville",
            dating_intent="serious_relationship",
            interests=interests,
        )

    def test_duplicate_interests_are_rejected(self) -> None:
        profile = self.create_profile(
            email="owner-interests@example.com",
            name="Profil propriétaire",
            interests=["music"],
        )

        serializer = ProfileSerializer(
            profile,
            data={
                "interests": [
                    "music",
                    "music",
                ],
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("interests", serializer.errors)

    def test_unknown_interest_is_rejected(self) -> None:
        profile = self.create_profile(
            email="invalid-interest@example.com",
            name="Profil invalide",
            interests=[],
        )

        serializer = ProfileSerializer(
            profile,
            data={"interests": ["unknown"]},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

    def test_discovery_exposes_common_interests_and_score(self) -> None:
        current = self.create_profile(
            email="current-interests@example.com",
            name="Profil actuel",
            interests=[
                "music",
                "football",
                "technology",
            ],
        )
        candidate = self.create_profile(
            email="candidate-interests@example.com",
            name="Profil candidat",
            interests=[
                "music",
                "technology",
                "travel",
            ],
        )

        request = APIRequestFactory().get("/api/v1/profiles/discovery/")
        request.user = current.user

        data = DiscoveryProfileSerializer(
            candidate,
            context={"request": request},
        ).data

        self.assertEqual(
            data["common_interests"],
            ["music", "technology"],
        )
        self.assertEqual(
            data["common_interest_labels"],
            ["Musique", "Technologie"],
        )
        self.assertEqual(data["compatibility_score"], 50)
        self.assertNotIn("email", data)
