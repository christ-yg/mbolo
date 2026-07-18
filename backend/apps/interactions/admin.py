from django.contrib import admin

from .models import (
    Interaction,
    Match,
)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    """
    Administration des interactions.

    Les adresses e-mail ne sont pas affichées
    dans la liste principale.
    """

    list_display = (
        "id",
        "actor_id",
        "target_profile_id",
        "decision",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "decision",
        "created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "actor__id",
        "target_profile__id",
    )


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    """
    Administration des matchs.
    """

    list_display = (
        "id",
        "profile_one_id",
        "profile_two_id",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "profile_one__id",
        "profile_two__id",
    )
