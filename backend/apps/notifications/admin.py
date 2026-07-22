
from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Vue administrative en lecture majoritaire.

    Les champs techniques permettent d'auditer les notifications
    sans exposer de mot de passe ni de jeton.
    """

    list_display = (
        "id",
        "recipient",
        "kind",
        "title",
        "is_read",
        "created_at",
    )
    list_filter = (
        "kind",
        "read_at",
        "created_at",
    )
    search_fields = (
        "recipient__email",
        "title",
        "source_key",
    )
    readonly_fields = (
        "id",
        "created_at",
    )
