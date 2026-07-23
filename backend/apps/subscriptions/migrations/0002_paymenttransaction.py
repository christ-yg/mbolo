import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentTransaction",
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
                    "method",
                    models.CharField(
                        choices=[
                            ("airtel_money", "Airtel Money"),
                            ("moov_money", "Moov Money"),
                            ("bank_card", "Carte bancaire"),
                        ],
                        max_length=24,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Créé"),
                            ("pending", "En attente"),
                            ("succeeded", "Réussi"),
                            ("failed", "Échoué"),
                            ("canceled", "Annulé"),
                            ("expired", "Expiré"),
                        ],
                        default="created",
                        max_length=24,
                    ),
                ),
                ("amount_xaf", models.PositiveIntegerField()),
                ("provider", models.CharField(blank=True, default="", max_length=48)),
                (
                    "provider_reference",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=128,
                    ),
                ),
                (
                    "idempotency_key",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("failure_code", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="premium_payments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "subscriptions_payment_transaction",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(
                fields=["user", "status", "created_at"],
                name="subscripti_user_id_313acc_idx",
            ),
        ),
    ]
