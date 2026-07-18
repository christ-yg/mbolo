from django.contrib import admin

from .models import Block


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """
    Administration des blocages.

    Les identifiants techniques sont affichés, mais pas les adresses
    e-mail dans la liste principale.
    """

    list_display = (
        "id",
        "blocker_id",
        "blocked_user_id",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "id",
        "blocker__id",
        "blocked_user__id",
    )

    readonly_fields = (
        "id",
        "created_at",
    )
