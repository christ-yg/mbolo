from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "plan",
        "status",
        "starts_at",
        "ends_at",
        "auto_renew",
    )
    list_filter = ("plan", "status", "auto_renew")
    search_fields = ("user__email", "provider_reference")
    readonly_fields = ("id", "created_at", "updated_at")
