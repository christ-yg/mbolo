from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    PremiumPrivacyPreference,
    ProfileBoost,
    PaymentMethod,
    PaymentStatus,
    PaymentTransaction,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)


@dataclass(frozen=True)
class PlanDefinition:
    code: str
    name: str
    description: str
    features: tuple[str, ...]


PLAN_CATALOG = (
    PlanDefinition(
        code="free",
        name="Mbolo Gratuit",
        description="L'essentiel pour créer de vraies connexions.",
        features=(
            "Profil et galerie de photos",
            "Découverte personnalisée",
            "Likes et matchs",
            "Messagerie entre matchs",
        ),
    ),
    PlanDefinition(
        code=SubscriptionPlan.PLUS,
        name="Mbolo Plus",
        description="Plus de contrôle sur tes rencontres.",
        features=(
            "Likes quotidiens illimités",
            "Voir les personnes qui t'ont liké",
            "Filtres de découverte avancés",
            "Retour sur le dernier profil ignoré",
            "1 Boost de 30 minutes tous les 7 jours",
            "1 Super Like par jour",
            "Accusés de lecture",
        ),
    ),
    PlanDefinition(
        code=SubscriptionPlan.PRESTIGE,
        name="Mbolo Prestige",
        description="L'expérience Mbolo la plus complète.",
        features=(
            "Tous les avantages Mbolo Plus",
            "Profil prioritaire dans Découvrir",
            "Mode navigation discrète",
            "2 Boosts de 30 minutes tous les 7 jours",
            "3 Super Likes par jour",
            "Support prioritaire",
        ),
    ),
)

FREE_ENTITLEMENTS = {
    "unlimited_likes": False,
    "see_likers": False,
    "advanced_filters": False,
    "rewind_pass": False,
    "read_receipts": False,
    "priority_profile": False,
    "incognito_mode": False,
    "priority_support": False,
    "profile_boost": False,
    "boosts_per_window": 0,
    "super_like": False,
    "super_likes_per_day": 0,
}

PLUS_ENTITLEMENTS = {
    **FREE_ENTITLEMENTS,
    "unlimited_likes": True,
    "see_likers": True,
    "advanced_filters": True,
    "rewind_pass": True,
    "read_receipts": True,
    "profile_boost": True,
    "boosts_per_window": 1,
    "super_like": True,
    "super_likes_per_day": 1,
}

PRESTIGE_ENTITLEMENTS = {
    **PLUS_ENTITLEMENTS,
    "priority_profile": True,
    "incognito_mode": True,
    "priority_support": True,
    "boosts_per_window": 2,
    "super_likes_per_day": 3,
}


def get_subscription_state(user) -> dict:
    try:
        subscription: Subscription | None = user.subscription
    except Subscription.DoesNotExist:
        subscription = None

    if subscription is None or not subscription.is_current:
        return {
            "plan": "free",
            "plan_name": "Mbolo Gratuit",
            "status": "none",
            "is_premium": False,
            "starts_at": None,
            "ends_at": None,
            "auto_renew": False,
            "entitlements": FREE_ENTITLEMENTS,
        }

    if subscription.plan == SubscriptionPlan.PRESTIGE:
        entitlements = PRESTIGE_ENTITLEMENTS
    else:
        entitlements = PLUS_ENTITLEMENTS

    return {
        "plan": subscription.plan,
        "plan_name": subscription.get_plan_display(),
        "status": subscription.status,
        "is_premium": True,
        "starts_at": subscription.starts_at,
        "ends_at": subscription.ends_at,
        "auto_renew": subscription.auto_renew,
        "entitlements": entitlements,
    }


def get_plan_catalog() -> list[dict]:
    prices = {
        SubscriptionPlan.PLUS: int(
            getattr(settings, "MBOLO_PLUS_PRICE_XAF", 0)
        ),
        SubscriptionPlan.PRESTIGE: int(
            getattr(settings, "MBOLO_PRESTIGE_PRICE_XAF", 0)
        ),
    }
    return [
        {
            "code": plan.code,
            "name": plan.name,
            "description": plan.description,
            "features": list(plan.features),
            "price_label": (
                "Gratuit"
                if plan.code == "free"
                else (
                    f"{prices[plan.code]:,} FCFA / mois".replace(",", " ")
                    if prices[plan.code] > 0
                    else "Tarif en cours de validation"
                )
            ),
            "amount_xaf": prices.get(plan.code, 0),
            "payment_available": bool(
                plan.code != "free"
                and prices.get(plan.code, 0) > 0
                and getattr(settings, "MBOLO_PAYMENT_PROVIDER", "")
            ),
        }
        for plan in PLAN_CATALOG
    ]


def get_payment_methods() -> list[dict]:
    configured = bool(getattr(settings, "MBOLO_PAYMENT_PROVIDER", ""))
    return [
        {
            "code": "airtel_money",
            "name": "Airtel Money",
            "description": (
                "Paiement depuis un portefeuille Airtel Money Gabon. "
                "La validation finale sera faite par confirmation serveur."
            ),
            "available": configured,
        },
        {
            "code": "moov_money",
            "name": "Moov Money",
            "description": (
                "Paiement depuis un portefeuille Moov Money Gabon. "
                "Mbolo ne demandera jamais le code PIN dans son interface."
            ),
            "available": configured,
        },
        {
            "code": "bank_card",
            "name": "Carte bancaire",
            "description": (
                "Visa ou Mastercard via la page sécurisée du prestataire. "
                "Le numéro complet et le CVV ne transitent pas par Mbolo."
            ),
            "available": configured,
        },
    ]


def get_privacy_state(user) -> dict:
    """
    Retourne la préférence enregistrée et son effet réel.

    effective_incognito devient automatiquement False lorsque Prestige
    expire, même si l'utilisateur avait activé le bouton auparavant.
    """

    preference, _created = (
        PremiumPrivacyPreference.objects.get_or_create(user=user)
    )
    subscription_state = get_subscription_state(user)
    entitled = bool(
        subscription_state["entitlements"]["incognito_mode"]
    )

    return {
        "incognito_enabled": preference.incognito_enabled,
        "incognito_available": entitled,
        "effective_incognito": (
            entitled and preference.incognito_enabled
        ),
    }


def update_incognito_preference(*, user, enabled: bool) -> dict:
    state = get_subscription_state(user)

    if not state["entitlements"]["incognito_mode"]:
        raise PermissionError(
            "Le mode discret nécessite un abonnement Mbolo Prestige actif."
        )

    preference, _created = (
        PremiumPrivacyPreference.objects.get_or_create(user=user)
    )
    preference.incognito_enabled = enabled
    preference.save(update_fields=("incognito_enabled", "updated_at"))
    return get_privacy_state(user)


BOOST_DURATION = timedelta(minutes=30)
BOOST_WINDOW = timedelta(days=7)


def get_boost_state(user, *, now=None) -> dict:
    """Calcule l'état depuis la base, sans faire confiance au navigateur."""

    now = now or timezone.now()
    subscription = get_subscription_state(user)
    entitlements = subscription["entitlements"]
    entitled = bool(entitlements["profile_boost"])
    allowance = int(entitlements["boosts_per_window"])
    window_start = now - BOOST_WINDOW
    used = ProfileBoost.objects.filter(
        user=user,
        starts_at__gte=window_start,
    ).count()
    active = (
        ProfileBoost.objects.filter(
            user=user,
            starts_at__lte=now,
            ends_at__gt=now,
        )
        .order_by("-ends_at")
        .first()
    )
    remaining = max(allowance - used, 0) if entitled else 0
    next_available_at = None
    if entitled and remaining == 0:
        oldest = (
            ProfileBoost.objects.filter(
                user=user,
                starts_at__gte=window_start,
            )
            .order_by("starts_at")
            .first()
        )
        if oldest:
            next_available_at = oldest.starts_at + BOOST_WINDOW

    return {
        "entitled": entitled,
        "active": active is not None,
        "active_until": active.ends_at if active else None,
        "duration_minutes": int(BOOST_DURATION.total_seconds() // 60),
        "allowance_per_7_days": allowance,
        "remaining": remaining,
        "next_available_at": next_available_at,
    }


@transaction.atomic
def activate_profile_boost(*, user) -> dict:
    """
    Active un Boost après verrouillage du compte.

    Le verrou empêche deux clics simultanés de consommer ou créer plusieurs
    activations au-delà du quota.
    """

    user_model = get_user_model()
    locked_user = user_model.objects.select_for_update().get(pk=user.pk)
    state = get_boost_state(locked_user)
    if not state["entitled"]:
        raise PermissionError("Un abonnement Mbolo Plus ou Prestige actif est requis.")
    if state["active"]:
        raise ValueError("Un Boost est déjà actif sur ce profil.")
    if state["remaining"] <= 0:
        raise ValueError("Ton quota de Boost est épuisé pour cette période.")

    now = timezone.now()
    ProfileBoost.objects.create(
        user=locked_user,
        starts_at=now,
        ends_at=now + BOOST_DURATION,
    )
    return get_boost_state(locked_user, now=now)


PAYMENT_DURATION = timedelta(days=30)


def is_payment_test_mode_enabled() -> bool:
    return bool(getattr(settings, "MBOLO_PAYMENT_TEST_MODE", False))


def get_plan_amount_xaf(plan: str) -> int:
    prices = {
        SubscriptionPlan.PLUS: int(
            getattr(settings, "MBOLO_PLUS_PRICE_XAF", 0)
        ),
        SubscriptionPlan.PRESTIGE: int(
            getattr(settings, "MBOLO_PRESTIGE_PRICE_XAF", 0)
        ),
    }
    amount = prices.get(plan, 0)
    if amount <= 0:
        raise ValueError("Le tarif de cette offre n'est pas encore configuré.")
    return amount


def serialize_payment_transaction(transaction: PaymentTransaction) -> dict:
    return {
        "id": transaction.id,
        "plan": transaction.plan,
        "plan_name": transaction.get_plan_display(),
        "method": transaction.method,
        "method_name": transaction.get_method_display(),
        "status": transaction.status,
        "amount_xaf": transaction.amount_xaf,
        "currency": "XAF",
        "provider": transaction.provider,
        "provider_reference": transaction.provider_reference,
        "created_at": transaction.created_at,
        "updated_at": transaction.updated_at,
        "verified_at": transaction.verified_at,
        "can_confirm_in_test_mode": (
            is_payment_test_mode_enabled()
            and transaction.status in {
                PaymentStatus.CREATED,
                PaymentStatus.PENDING,
            }
        ),
    }


@transaction.atomic
def create_payment_checkout(*, user, plan: str, method: str) -> PaymentTransaction:
    """
    Crée une transaction locale avec un montant décidé exclusivement côté serveur.

    En mode test, aucun prestataire externe n'est contacté. En production, cette
    fonction devra déléguer l'initialisation à un adaptateur de paiement dédié.
    """

    if plan not in {SubscriptionPlan.PLUS, SubscriptionPlan.PRESTIGE}:
        raise ValueError("Offre Premium invalide.")

    if method not in {
        PaymentMethod.AIRTEL_MONEY,
        PaymentMethod.MOOV_MONEY,
        PaymentMethod.BANK_CARD,
    }:
        raise ValueError("Moyen de paiement invalide.")

    amount = get_plan_amount_xaf(plan)
    provider = (
        "mbolo_test"
        if is_payment_test_mode_enabled()
        else str(getattr(settings, "MBOLO_PAYMENT_PROVIDER", "")).strip()
    )
    if not provider:
        raise RuntimeError(
            "Le prestataire de paiement n'est pas encore configuré."
        )

    transaction_obj = PaymentTransaction.objects.create(
        user=user,
        plan=plan,
        method=method,
        status=PaymentStatus.PENDING,
        amount_xaf=amount,
        provider=provider,
    )
    transaction_obj.provider_reference = f"{provider}:{transaction_obj.id}"
    transaction_obj.save(
        update_fields=("provider_reference", "updated_at")
    )
    return transaction_obj


@transaction.atomic
def confirm_test_payment(*, user, transaction_id) -> tuple[PaymentTransaction, Subscription]:
    """
    Confirme une transaction uniquement lorsque le mode test est activé.

    Cette route simule la confirmation serveur d'un prestataire. Elle ne doit
    jamais être utilisée en production à la place d'un webhook signé.
    """

    if not is_payment_test_mode_enabled():
        raise PermissionError(
            "La confirmation manuelle est disponible uniquement en mode test."
        )

    payment = (
        PaymentTransaction.objects.select_for_update()
        .filter(id=transaction_id, user=user)
        .first()
    )
    if payment is None:
        raise LookupError("Transaction introuvable.")

    if payment.status == PaymentStatus.SUCCEEDED:
        subscription = Subscription.objects.get(user=user)
        return payment, subscription

    if payment.status not in {
        PaymentStatus.CREATED,
        PaymentStatus.PENDING,
    }:
        raise ValueError(
            "Cette transaction ne peut plus être confirmée."
        )

    expected_amount = get_plan_amount_xaf(payment.plan)
    if payment.amount_xaf != expected_amount:
        payment.status = PaymentStatus.FAILED
        payment.failure_code = "amount_mismatch"
        payment.save(
            update_fields=(
                "status",
                "failure_code",
                "updated_at",
            )
        )
        raise ValueError("Le montant de la transaction est invalide.")

    now = timezone.now()
    payment.status = PaymentStatus.SUCCEEDED
    payment.verified_at = now
    payment.failure_code = ""
    payment.save(
        update_fields=(
            "status",
            "verified_at",
            "failure_code",
            "updated_at",
        )
    )

    subscription, _created = Subscription.objects.select_for_update().get_or_create(
        user=user,
        defaults={
            "plan": payment.plan,
            "status": SubscriptionStatus.ACTIVE,
            "starts_at": now,
            "ends_at": now + PAYMENT_DURATION,
            "auto_renew": False,
            "provider_reference": payment.provider_reference,
        },
    )
    subscription.plan = payment.plan
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.starts_at = now
    subscription.ends_at = now + PAYMENT_DURATION
    subscription.auto_renew = False
    subscription.provider_reference = payment.provider_reference
    subscription.save(
        update_fields=(
            "plan",
            "status",
            "starts_at",
            "ends_at",
            "auto_renew",
            "provider_reference",
            "updated_at",
        )
    )

    return payment, subscription


@transaction.atomic
def cancel_payment(*, user, transaction_id) -> PaymentTransaction:
    payment = (
        PaymentTransaction.objects.select_for_update()
        .filter(id=transaction_id, user=user)
        .first()
    )
    if payment is None:
        raise LookupError("Transaction introuvable.")

    if payment.status == PaymentStatus.SUCCEEDED:
        raise ValueError(
            "Une transaction déjà confirmée ne peut pas être annulée."
        )

    if payment.status in {
        PaymentStatus.CANCELED,
        PaymentStatus.FAILED,
        PaymentStatus.EXPIRED,
    }:
        return payment

    payment.status = PaymentStatus.CANCELED
    payment.save(update_fields=("status", "updated_at"))
    return payment


def get_payment_history(user, *, limit: int = 20) -> list[dict]:
    transactions = PaymentTransaction.objects.filter(user=user)[:limit]
    return [
        serialize_payment_transaction(item)
        for item in transactions
    ]
