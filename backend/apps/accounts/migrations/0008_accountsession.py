from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_accountsecurityevent"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountSession",
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
                    "session_key_hash",
                    models.CharField(
                        editable=False,
                        max_length=64,
                        unique=True,
                    ),
                ),
                (
                    "device",
                    models.CharField(
                        default="Appareil inconnu",
                        max_length=120,
                    ),
                ),
                (
                    "ip_fingerprint",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=16,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "last_seen_at",
                    models.DateTimeField(
                        auto_now=True,
                        db_index=True,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account_sessions",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "ordering": ("-last_seen_at",),
            },
        ),
        migrations.AddIndex(
            model_name="accountsession",
            index=models.Index(
                fields=["user", "-last_seen_at"],
                name="acct_sess_user_seen_idx",
            ),
        ),
    ]
