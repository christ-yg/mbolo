from django.contrib import admin

from .models import (
    PaymentTransaction,
    PremiumPrivacyPreference,
    ProfileBoost,
    Subscription,
)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "plan",
        "status",
        "starts_at",
        "ends_at",
        "auto_renew",
    )
    list_filter = ("plan", "status", "auto_renew")
    search_fields = ("user__email", "provider_reference")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "plan",
        "method",
        "status",
        "amount_xaf",
        "provider",
        "created_at",
        "verified_at",
    )
    list_filter = ("plan", "method", "status", "provider")
    search_fields = (
        "user__email",
        "provider_reference",
        "idempotency_key",
    )
    readonly_fields = (
        "id",
        "idempotency_key",
        "created_at",
        "updated_at",
        "verified_at",
    )


@admin.register(ProfileBoost)
class ProfileBoostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "starts_at", "ends_at")
    search_fields = ("user__email",)
    readonly_fields = ("id", "created_at")


@admin.register(PremiumPrivacyPreference)
class PremiumPrivacyPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "incognito_enabled", "updated_at")
    search_fields = ("user__email",)
