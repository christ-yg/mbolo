"""
Administration Django des photos de profil.

L'administration sert uniquement aux personnes autorisées.

En production, les comptes administratifs devront respecter :

- le principe du moindre privilège ;
- une authentification forte ;
- une revue périodique des accès ;
- une journalisation des actions ;
- idéalement une authentification multifacteur.
"""

from django.contrib import admin
from django.utils import timezone

from .models import ProfilePhoto


@admin.register(ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    """
    Administration des photos de profil.
    """

    list_display = (
        "id",
        "profile_id",
        "position",
        "is_primary",
        "moderation_status",
        "reviewed_at",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_primary",
        "moderation_status",
        "position",
        "created_at",
    )

    search_fields = (
        "id",
        "profile__id",
        "profile__user__id",
    )

    readonly_fields = (
        "id",
        "profile",
        "image",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "profile",
        "profile__user",
    )

    actions = ("approve_photos", "reject_photos")

    @admin.action(description="Approuver les photos sélectionnées")
    def approve_photos(self, request, queryset):
        queryset.update(
            moderation_status=ProfilePhoto.ModerationStatus.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description="Refuser les photos sélectionnées")
    def reject_photos(self, request, queryset):
        queryset.update(
            moderation_status=ProfilePhoto.ModerationStatus.REJECTED,
            is_primary=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    def get_queryset(self, request):
        """
        Charge le profil et son utilisateur en une seule requête SQL.

        Cela évite le problème N+1 dans l'administration.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "profile",
                "profile__user",
            )
        )
