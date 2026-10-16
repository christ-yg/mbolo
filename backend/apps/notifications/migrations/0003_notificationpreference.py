import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("notifications", "0002_alter_notification_kind"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("notifications_enabled", models.BooleanField(default=True)),
                ("messages_enabled", models.BooleanField(default=True)),
                ("matches_enabled", models.BooleanField(default=True)),
                ("likes_enabled", models.BooleanField(default=True)),
                ("quiet_hours_enabled", models.BooleanField(default=False)),
                ("quiet_start", models.TimeField(default=datetime.time(22, 0))),
                ("quiet_end", models.TimeField(default=datetime.time(7, 0))),
                (
                    "timezone_offset_minutes",
                    models.SmallIntegerField(
                        default=60,
                        validators=[
                            django.core.validators.MinValueValidator(-720),
                            django.core.validators.MaxValueValidator(840),
                        ],
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_preference",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "notifications_preference"},
        ),
    ]
