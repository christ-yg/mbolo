from django.contrib import admin

from .models import (
    Profile,
    SearchPreferences,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Administration des profils publics.
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


@admin.register(SearchPreferences)
class SearchPreferencesAdmin(
    admin.ModelAdmin
):
    """
    Administration limitée des préférences privées.

    Les adresses e-mail ne sont pas affichées dans les listes.
    """

    list_display = (
        "id",
        "minimum_age",
        "maximum_age",
        "maximum_distance_km",
        "only_verified_profiles",
        "created_at",
    )

    list_filter = (
        "only_verified_profiles",
        "minimum_age",
        "maximum_age",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
