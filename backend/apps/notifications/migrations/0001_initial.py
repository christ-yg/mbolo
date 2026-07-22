
# Generated manually for the Mbolo notification center.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("message", "Message"),
                            ("match", "Nouveau match"),
                            ("like", "Like"),
                            ("security", "Sécurité"),
                            ("system", "Système"),
                        ],
                        db_index=True,
                        max_length=24,
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=120),
                ),
                (
                    "body",
                    models.CharField(blank=True, default="", max_length=240),
                ),
                (
                    "target_path",
                    models.CharField(blank=True, default="", max_length=500),
                ),
                (
                    "source_key",
                    models.CharField(max_length=160),
                ),
                (
                    "metadata",
                    models.JSONField(blank=True, default=dict),
                ),
                (
                    "read_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        null=True,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "notifications_notification",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                fields=("recipient", "source_key"),
                name="notification_recipient_source_unique",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["recipient", "read_at", "-created_at"],
                name="notif_user_read_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["recipient", "kind", "-created_at"],
                name="notif_user_kind_created_idx",
            ),
        ),
    ]
