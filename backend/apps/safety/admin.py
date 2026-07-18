"""
Configuration de l'administration Django du module Safety.

L'administration permet aux personnes autorisées de consulter
les blocages et de traiter les signalements.

Attention :

L'administration Django ne remplace pas une politique de contrôle
des accès. Les comptes administratifs devront être protégés par :

- privilèges minimaux ;
- mots de passe robustes ;
- authentification multifacteur en production ;
- journalisation ;
- revue périodique des droits.
"""

from django.contrib import admin

from .models import (
    Block,
    Report,
    ReportStatus,
)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """
    Administration des blocages utilisateurs.

    Les e-mails ne sont pas affichés dans la liste principale.
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

    ordering = (
        "-created_at",
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Administration et workflow des signalements.

    Les champs techniques et de traçabilité sont visibles,
    mais les modifications sensibles restent contrôlées.
    """

    list_display = (
        "id",
        "reason",
        "status",
        "reporter_id",
        "reported_user_id",
        "reviewed_by_id",
        "created_at",
        "resolved_at",
    )

    list_filter = (
        "status",
        "reason",
        "created_at",
        "resolved_at",
    )

    search_fields = (
        "id",
        "reporter__id",
        "reported_user__id",
        "reviewed_by__id",
    )

    readonly_fields = (
        "id",
        "reporter",
        "reported_user",
        "reason",
        "description",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"

    list_select_related = (
        "reporter",
        "reported_user",
        "reviewed_by",
    )

    fieldsets = (
        (
            "Signalement",
            {
                "fields": (
                    "id",
                    "reporter",
                    "reported_user",
                    "reason",
                    "description",
                )
            },
        ),
        (
            "Traitement de modération",
            {
                "fields": (
                    "status",
                    "reviewed_by",
                    "moderator_note",
                    "resolved_at",
                )
            },
        ),
        (
            "Traçabilité",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_queryset(self, request):
        """
        Charge les relations utilisateur en une seule requête SQL.

        Cela évite plusieurs requêtes supplémentaires pour chaque ligne
        affichée dans l'administration.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "reporter",
                "reported_user",
                "reviewed_by",
            )
        )

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        """
        Empêche la modification de certains champs après résolution.

        Un dossier finalisé conserve ainsi une meilleure intégrité
        historique.
        """

        readonly_fields = list(
            super().get_readonly_fields(
                request,
                obj,
            )
        )

        if (
            obj is not None
            and obj.status
            in {
                ReportStatus.RESOLVED,
                ReportStatus.REJECTED,
            }
        ):
            readonly_fields.extend(
                [
                    "status",
                    "reviewed_by",
                    "moderator_note",
                    "resolved_at",
                ]
            )

        return tuple(
            dict.fromkeys(
                readonly_fields
            )
        )
