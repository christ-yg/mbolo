import django.db.models.deletion
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_email_2fa_enabled"),
    ]

    operations = [
        migrations.CreateModel(
            name="LoginActivity",
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
                    "method",
                    models.CharField(
                        choices=[
                            ("password", "Mot de passe"),
                            (
                                "email_2fa",
                                "Double authentification e-mail",
                            ),
                        ],
                        max_length=32,
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
                        help_text=(
                            "Empreinte irréversible et tronquée, "
                            "jamais l'adresse IP."
                        ),
                        max_length=16,
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
                        related_name="login_activities",
                        to="accounts.user",
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddIndex(
            model_name="loginactivity",
            index=models.Index(
                fields=["user", "-created_at"],
                name="account_login_user_created_idx",
            ),
        ),
    ]
