"""Tests du workflow privé de vérification des profils Mbolo."""

from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.photos.models import ProfilePhoto

from .models import Profile, ProfileVerification
from .serializers import DiscoveryProfileSerializer
from .storage import PrivateVerificationStorage


User = get_user_model()


def image_file(name: str = "selfie.jpg") -> SimpleUploadedFile:
    buffer = BytesIO()
    image = Image.new("RGB", (640, 640), (90, 70, 120))
    image.save(buffer, format="JPEG")
    image.close()
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type="image/jpeg",
    )


class ProfileVerificationTests(TestCase):
    def setUp(self):
        self.private_directory = TemporaryDirectory()
        self.override = override_settings(
            PRIVATE_VERIFICATION_MEDIA_ROOT=self.private_directory.name,
        )
        self.override.enable()
        self.selfie_field = ProfileVerification._meta.get_field("selfie")
        self.original_storage = self.selfie_field.storage
        self.selfie_field.storage = PrivateVerificationStorage()

        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            email="verification-profile@example.com",
            password="Strong-Verification-Password-2026!",
            is_email_verified=True,
        )
        self.profile = Profile.objects.create(
            user=self.user,
            display_name="Membre Vérifié",
            birth_date=date(1995, 5, 12),
            gender="man",
            city="libreville",
            biography="Profil complet utilisé pendant les tests.",
            dating_intent="serious_relationship",
            is_discoverable=True,
        )
        ProfilePhoto.objects.create(
            profile=self.profile,
            image=image_file("primary.jpg"),
            position=0,
            is_primary=True,
        )
        self.url = reverse("profiles:current-profile-verification")
        self.csrf_url = reverse("core:csrf-token")

    def tearDown(self):
        self.selfie_field.storage = self.original_storage
        self.override.disable()
        self.private_directory.cleanup()

    def authenticate(self) -> str:
        self.client.force_login(self.user)
        response = self.client.get(self.csrf_url)
        return response.data["csrfToken"]

    def test_anonymous_user_cannot_read_verification(self):
        response = self.client.get(self.url)
        self.assertIn(
            response.status_code,
            {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
        )

    def test_submission_requires_csrf(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {"selfie": image_file()},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_valid_selfie_becomes_private_pending_request(self):
        csrf = self.authenticate()
        response = self.client.post(
            self.url,
            {"selfie": image_file("unsafe-original-name.jpg")},
            format="multipart",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")
        self.assertNotIn("selfie", response.data)

        verification = ProfileVerification.objects.get(profile=self.profile)
        self.assertTrue(verification.selfie.name.endswith(".webp"))
        self.assertNotIn("unsafe-original-name", verification.selfie.name)
        self.assertTrue(verification.selfie.storage.exists(verification.selfie.name))

    def test_pending_request_cannot_be_duplicated(self):
        csrf = self.authenticate()
        first = self.client.post(
            self.url,
            {"selfie": image_file()},
            format="multipart",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(
            self.url,
            {"selfie": image_file("second.jpg")},
            format="multipart",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            ProfileVerification.objects.filter(profile=self.profile).count(),
            1,
        )

    def test_email_verification_alone_does_not_grant_public_badge(self):
        payload = DiscoveryProfileSerializer(self.profile).data
        self.assertFalse(payload["is_verified"])

        ProfileVerification.objects.create(
            profile=self.profile,
            status=ProfileVerification.Status.APPROVED,
        )
        payload = DiscoveryProfileSerializer(self.profile).data
        self.assertTrue(payload["is_verified"])

    def test_get_never_exposes_private_file(self):
        self.authenticate()
        ProfileVerification.objects.create(
            profile=self.profile,
            status=ProfileVerification.Status.REJECTED,
            selfie=image_file(),
            rejection_reason="Photo trop sombre.",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("selfie", response.data)
        self.assertNotIn("image_url", response.data)
