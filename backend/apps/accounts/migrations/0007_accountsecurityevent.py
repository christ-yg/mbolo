from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_user_login_alert_emails_enabled"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountSecurityEvent",
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
                    "event",
                    models.CharField(max_length=64),
                ),
                (
                    "outcome",
                    models.CharField(max_length=32),
                ),
                (
                    "reason",
                    models.CharField(
                        default="not_applicable",
                        max_length=64,
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
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="security_events",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="accountsecurityevent",
            index=models.Index(
                fields=["user", "-created_at"],
                name="acct_sec_user_created_idx",
            ),
        ),
    ]
