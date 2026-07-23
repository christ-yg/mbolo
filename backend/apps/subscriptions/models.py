from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.TextChoices):
    PLUS = "plus", "Mbolo Plus"
    PRESTIGE = "prestige", "Mbolo Prestige"


class SubscriptionStatus(models.TextChoices):
    TRIAL = "trial", "Essai"
    ACTIVE = "active", "Actif"
    CANCELED = "canceled", "Résilié"
    EXPIRED = "expired", "Expiré"


class PaymentMethod(models.TextChoices):
    AIRTEL_MONEY = "airtel_money", "Airtel Money"
    MOOV_MONEY = "moov_money", "Moov Money"
    BANK_CARD = "bank_card", "Carte bancaire"


class PaymentStatus(models.TextChoices):
    CREATED = "created", "Créé"
    PENDING = "pending", "En attente"
    SUCCEEDED = "succeeded", "Réussi"
    FAILED = "failed", "Échoué"
    CANCELED = "canceled", "Annulé"
    EXPIRED = "expired", "Expiré"


class Subscription(models.Model):
    """
    Source de vérité serveur d'un abonnement.
    Aucun champ de carte bancaire ni secret de paiement n'est stocké ici.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.CharField(
        max_length=24,
        choices=SubscriptionPlan.choices,
    )
    status = models.CharField(
        max_length=24,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    provider_reference = models.CharField(
        max_length=128,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions_subscription"
        ordering = ("-created_at",)

    @property
    def is_current(self) -> bool:
        if self.status not in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
        }:
            return False
        return self.ends_at is None or self.ends_at > timezone.now()

    def __str__(self) -> str:
        return f"Subscription<{self.id}:{self.plan}:{self.status}>"


class PaymentTransaction(models.Model):
    """
    Trace locale d'une tentative de paiement.

    Le montant et l'offre sont décidés par le serveur. Les secrets Airtel/Moov,
    le code OTP, le PIN Mobile Money, le PAN et le CVV ne sont jamais stockés.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="premium_payments",
    )
    plan = models.CharField(max_length=24, choices=SubscriptionPlan.choices)
    method = models.CharField(max_length=24, choices=PaymentMethod.choices)
    status = models.CharField(
        max_length=24,
        choices=PaymentStatus.choices,
        default=PaymentStatus.CREATED,
    )
    amount_xaf = models.PositiveIntegerField()
    provider = models.CharField(max_length=48, blank=True, default="")
    provider_reference = models.CharField(
        max_length=128, blank=True, default="", db_index=True
    )
    idempotency_key = models.UUIDField(default=uuid4, unique=True, editable=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions_payment_transaction"
        ordering = ("-created_at",)
        indexes = [
            # Nom explicite : évite que Django propose une migration de
            # renommage différente selon la longueur calculée automatiquement.
            models.Index(
                fields=("user", "status", "created_at"),
                name="subscripti_user_id_313acc_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"PaymentTransaction<{self.id}:{self.method}:{self.status}>"
