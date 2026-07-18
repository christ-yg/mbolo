from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Administration minimale des profils.

    L'e-mail n'est pas utilisé comme représentation textuelle
    afin de limiter son exposition dans les interfaces.
    """

    list_display = (
        "id",
        "display_name",
        "city",
        "dating_intent",
        "is_discoverable",
        "created_at",
    )

    list_filter = (
        "city",
        "gender",
        "dating_intent",
        "is_discoverable",
    )

    search_fields = (
        "display_name",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
