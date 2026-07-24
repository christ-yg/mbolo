from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    PremiumPrivacyPreference,
    ProfileBoost,
    Subscription,
    SubscriptionPlan,
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
