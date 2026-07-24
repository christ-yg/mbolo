from dataclasses import dataclass

from django.conf import settings

from .models import (
    PremiumPrivacyPreference,
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
}

PLUS_ENTITLEMENTS = {
    **FREE_ENTITLEMENTS,
    "unlimited_likes": True,
    "see_likers": True,
    "advanced_filters": True,
    "rewind_pass": True,
    "read_receipts": True,
}

PRESTIGE_ENTITLEMENTS = {
    **PLUS_ENTITLEMENTS,
    "priority_profile": True,
    "incognito_mode": True,
    "priority_support": True,
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
