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
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_primary",
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
