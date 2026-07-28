from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    PaymentStatus,
    PaymentTransaction,
    PremiumPrivacyPreference,
    ProfileBoost,
    Subscription,
    SubscriptionStatus,
)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "status_badge",
        "starts_at",
        "ends_at",
        "auto_renew",
    )
    list_filter = ("plan", "status", "auto_renew", "created_at")
    search_fields = ("user__email", "user__id", "provider_reference")
    readonly_fields = (
        "id",
        "user",
        "provider_reference",
        "created_at",
        "updated_at",
    )
    list_select_related = ("user",)
    actions = ("cancel_subscriptions", "expire_subscriptions")

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, subscription):
        css = {
            SubscriptionStatus.ACTIVE: "approved",
            SubscriptionStatus.TRIAL: "pending",
            SubscriptionStatus.CANCELED: "neutral",
            SubscriptionStatus.EXPIRED: "rejected",
        }.get(subscription.status, "neutral")
        return format_html(
            '<span class="mbolo-status mbolo-status--{}">{}</span>',
            css,
            subscription.get_status_display(),
        )

    @admin.action(description="Résilier les abonnements sélectionnés")
    def cancel_subscriptions(self, request, queryset):
        changed = queryset.exclude(
            status=SubscriptionStatus.CANCELED
        ).update(
            status=SubscriptionStatus.CANCELED,
            auto_renew=False,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{changed} abonnement(s) résilié(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Marquer comme expirés")
    def expire_subscriptions(self, request, queryset):
        changed = queryset.exclude(
            status=SubscriptionStatus.EXPIRED
        ).update(
            status=SubscriptionStatus.EXPIRED,
            auto_renew=False,
            ends_at=timezone.now(),
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{changed} abonnement(s) expiré(s).",
            level=messages.WARNING,
        )

    class Media:
        css = {"all": ("admin/css/mbolo_admin.css",)}


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "short_id",
        "user",
        "plan",
        "method",
        "status_badge",
        "amount_xaf",
        "provider",
        "created_at",
        "verified_at",
    )
    list_filter = ("plan", "method", "status", "provider", "created_at")
    search_fields = (
        "id",
        "user__email",
        "user__id",
        "provider_reference",
        "idempotency_key",
    )
    readonly_fields = (
        "id",
        "user",
        "plan",
        "method",
        "amount_xaf",
        "provider",
        "provider_reference",
        "idempotency_key",
        "verified_at",
        "failure_code",
        "created_at",
        "updated_at",
    )
    list_select_related = ("user",)
    date_hierarchy = "created_at"
    actions = ("expire_pending_transactions",)

    @admin.display(description="Transaction")
    def short_id(self, payment):
        return str(payment.id).split("-")[0].upper()

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, payment):
        css = {
            PaymentStatus.SUCCEEDED: "approved",
            PaymentStatus.PENDING: "pending",
            PaymentStatus.CREATED: "pending",
            PaymentStatus.CANCELED: "neutral",
            PaymentStatus.FAILED: "rejected",
            PaymentStatus.EXPIRED: "rejected",
        }.get(payment.status, "neutral")
        return format_html(
            '<span class="mbolo-status mbolo-status--{}">{}</span>',
            css,
            payment.get_status_display(),
        )

    @admin.action(description="Expirer les transactions en attente")
    def expire_pending_transactions(self, request, queryset):
        changed = queryset.filter(
            status__in=(PaymentStatus.CREATED, PaymentStatus.PENDING)
        ).update(
            status=PaymentStatus.EXPIRED,
            failure_code="expired_by_admin",
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{changed} transaction(s) expirée(s).",
            level=messages.WARNING,
        )

    def has_add_permission(self, request):
        return False

    class Media:
        css = {"all": ("admin/css/mbolo_admin.css",)}


@admin.register(ProfileBoost)
class ProfileBoostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "starts_at", "ends_at", "active_badge")
    search_fields = ("user__email", "user__id")
    readonly_fields = ("id", "user", "starts_at", "ends_at", "created_at")
    list_select_related = ("user",)

    @admin.display(description="État")
    def active_badge(self, boost):
        css = "approved" if boost.is_active else "neutral"
        label = "Actif" if boost.is_active else "Terminé"
        return format_html(
            '<span class="mbolo-status mbolo-status--{}">{}</span>',
            css,
            label,
        )

    def has_add_permission(self, request):
        return False


@admin.register(PremiumPrivacyPreference)
class PremiumPrivacyPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "incognito_enabled", "updated_at")
    search_fields = ("user__email", "user__id")
    readonly_fields = ("user", "incognito_enabled", "updated_at")

    def has_add_permission(self, request):
        return False
