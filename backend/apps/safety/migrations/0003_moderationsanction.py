import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_suspension_until"),
        ("safety", "0002_report"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ModerationSanction",
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
                    "sanction_type",
                    models.CharField(
                        choices=[
                            ("warning", "Avertissement"),
                            ("suspension_7_days", "Suspension de 7 jours"),
                            ("suspension_30_days", "Suspension de 30 jours"),
                            (
                                "permanent_suspension",
                                "Suspension sans échéance",
                            ),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                (
                    "internal_note",
                    models.TextField(
                        blank=True,
                        default="",
                        max_length=2000,
                    ),
                ),
                (
                    "expires_at",
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
                    "moderator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="issued_moderation_sanctions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sanctions",
                        to="safety.report",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="moderation_sanctions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "safety_moderation_sanction",
                "ordering": ("-created_at",),
                "indexes": [
                    models.Index(
                        fields=["user", "-created_at"],
                        name="sanction_user_created_idx",
                    ),
                    models.Index(
                        fields=["report", "-created_at"],
                        name="sanction_report_created_idx",
                    ),
                ],
            },
        ),
    ]
