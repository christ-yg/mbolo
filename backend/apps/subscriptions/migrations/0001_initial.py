import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Subscription",
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
                    "plan",
                    models.CharField(
                        choices=[
                            ("plus", "Mbolo Plus"),
                            ("prestige", "Mbolo Prestige"),
                        ],
                        max_length=24,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("trial", "Essai"),
                            ("active", "Actif"),
                            ("canceled", "Résilié"),
                            ("expired", "Expiré"),
                        ],
                        default="active",
                        max_length=24,
                    ),
                ),
                (
                    "starts_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("auto_renew", models.BooleanField(default=False)),
                (
                    "provider_reference",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscription",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "subscriptions_subscription",
                "ordering": ("-created_at",),
            },
        ),
    ]
