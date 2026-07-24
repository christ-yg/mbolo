import uuid

import apps.profiles.models
import apps.profiles.storage
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0004_profile_interests"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfileVerification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("not_submitted", "Non demandée"),
                            ("pending", "En attente"),
                            ("approved", "Approuvée"),
                            ("rejected", "Refusée"),
                        ],
                        db_index=True,
                        default="not_submitted",
                        max_length=24,
                    ),
                ),
                (
                    "selfie",
                    models.ImageField(
                        blank=True,
                        max_length=500,
                        storage=apps.profiles.storage.PrivateVerificationStorage(),
                        upload_to=apps.profiles.models.verification_selfie_upload_path,
                    ),
                ),
                (
                    "rejection_reason",
                    models.CharField(blank=True, default="", max_length=240),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verification",
                        to="profiles.profile",
                    ),
                ),
            ],
            options={
                "db_table": "profiles_profile_verification",
                "ordering": ("-updated_at",),
            },
        ),
    ]
