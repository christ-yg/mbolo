from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.profiles.models import DatingIntent, Profile
from apps.profiles.serializers import DiscoveryProfileSerializer

from ..models import ProfilePhoto
from ..services import create_profile_photo, update_profile_photo


User = get_user_model()


def image_file():
    buffer = BytesIO()
    Image.new("RGB", (640, 640), (130, 70, 110)).save(
        buffer, format="JPEG"
    )
    return SimpleUploadedFile(
        "portrait.jpg", buffer.getvalue(), content_type="image/jpeg"
    )


class PhotoModerationTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media.name,
            PROFILE_PHOTO_MAX_COUNT=6,
            PROFILE_PHOTO_MAX_BYTES=8 * 1024 * 1024,
            PROFILE_PHOTO_MIN_WIDTH=320,
            PROFILE_PHOTO_MIN_HEIGHT=320,
            PROFILE_PHOTO_MAX_WIDTH=6000,
            PROFILE_PHOTO_MAX_HEIGHT=6000,
            PROFILE_PHOTO_OUTPUT_MAX_WIDTH=1600,
            PROFILE_PHOTO_OUTPUT_MAX_HEIGHT=1600,
            PROFILE_PHOTO_WEBP_QUALITY=88,
        )
        self.settings_override.enable()
        self.user = User.objects.create_user(
            email="moderation-photo@example.com",
            password="Strong-Photo-Moderation-2026!",
            is_email_verified=True,
        )
        self.profile = Profile.objects.create(
            user=self.user,
            display_name="Ariane",
            birth_date=date(1994, 1, 1),
            gender="woman",
            city="libreville",
            biography="Une biographie publique suffisamment complète.",
            dating_intent=DatingIntent.SERIOUS_RELATIONSHIP,
            is_discoverable=True,
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media.cleanup()

    def test_new_upload_is_pending(self):
        result = create_profile_photo(
            user=self.user,
            uploaded_file=image_file(),
        )
        self.assertEqual(
            result.photo.moderation_status,
            ProfilePhoto.ModerationStatus.PENDING,
        )

    def test_pending_photo_is_not_public(self):
        create_profile_photo(
            user=self.user,
            uploaded_file=image_file(),
        )
        data = DiscoveryProfileSerializer(self.profile).data
        self.assertEqual(data["photos"], [])

    def test_pending_photo_can_be_primary_but_stays_private(self):
        create_profile_photo(
            user=self.user,
            uploaded_file=image_file(),
        )
        photo = create_profile_photo(
            user=self.user,
            uploaded_file=image_file(),
        ).photo
        updated = update_profile_photo(
            user=self.user,
            photo_id=photo.id,
            is_primary=True,
        )
        self.assertTrue(updated.is_primary)
        self.assertEqual(
            DiscoveryProfileSerializer(self.profile).data["photos"],
            [],
        )

    def test_approved_photo_is_public(self):
        photo = create_profile_photo(
            user=self.user,
            uploaded_file=image_file(),
        ).photo
        photo.moderation_status = ProfilePhoto.ModerationStatus.APPROVED
        photo.save(update_fields=["moderation_status", "updated_at"])
        data = DiscoveryProfileSerializer(self.profile).data
        self.assertEqual(len(data["photos"]), 1)
