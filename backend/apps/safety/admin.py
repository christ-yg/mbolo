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
from django.db import transaction
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from django.utils.html import format_html

from apps.notifications.services import (
    broadcast_notification_created,
    create_moderation_sanction_notification,
    create_report_status_notification,
)

from .models import (
    Block,
    ModerationSanction,
    ModerationSanctionType,
    Report,
    ReportStatus,
    SanctionAppeal,
    SanctionAppealStatus,
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
        "short_id",
        "reason",
        "status_badge",
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

    actions = (
        "mark_under_review",
        "mark_resolved",
        "mark_rejected",
        "warn_reported_users",
        "suspend_reported_users_7_days",
        "suspend_reported_users_30_days",
        "suspend_reported_users_permanently",
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

    @admin.display(description="Dossier")
    def short_id(self, report: Report) -> str:
        """
        Affiche un identifiant court, tout en conservant l'UUID complet
        dans la page de détail.
        """

        return str(report.id).split("-")[0]

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, report: Report):
        """
        Rend l'état du dossier immédiatement lisible dans la file.
        """

        colors = {
            ReportStatus.PENDING: ("#7d2148", "#f6dce7"),
            ReportStatus.UNDER_REVIEW: ("#7a4d00", "#fff0c7"),
            ReportStatus.RESOLVED: ("#087c4e", "#dff5e9"),
            ReportStatus.REJECTED: ("#5d555a", "#ece8eb"),
        }
        foreground, background = colors[report.status]

        return format_html(
            '<span style="display:inline-block;padding:5px 10px;'
            'border-radius:999px;font-weight:800;color:{};background:{}">{}</span>',
            foreground,
            background,
            report.get_status_display(),
        )

    def _transition_reports(
        self,
        *,
        request,
        queryset,
        destination: str,
    ) -> int:
        """
        Applique une transition dossier par dossier.

        Nous utilisons save() plutôt qu'un update SQL massif afin de
        conserver les validations métier définies dans le modèle.
        """

        changed = 0
        finalized_statuses = {
            ReportStatus.RESOLVED,
            ReportStatus.REJECTED,
        }

        with transaction.atomic():
            for report in queryset.select_for_update():
                if report.status in finalized_statuses:
                    continue

                report.status = destination
                report.reviewed_by = request.user
                report.resolved_at = (
                    timezone.now()
                    if destination in finalized_statuses
                    else None
                )
                report.save()

                notification_result = (
                    create_report_status_notification(
                        recipient=report.reporter,
                        report_id=report.id,
                        status=destination,
                    )
                )
                if notification_result.created:
                    notification = notification_result.notification
                    transaction.on_commit(
                        lambda notification=notification: (
                            broadcast_notification_created(
                                notification=notification,
                                event_name="report.notification",
                            )
                        )
                    )
                changed += 1

        return changed

    def _sanction_reported_users(
        self,
        *,
        request,
        queryset,
        sanction_type: str,
    ) -> tuple[int, int]:
        """
        Applique une mesure aux membres signalés avec journalisation.

        Les comptes staff et superutilisateurs sont ignorés afin qu'une
        sélection administrative en masse ne puisse pas désactiver un
        compte privilégié.
        """

        durations = {
            ModerationSanctionType.WARNING: None,
            ModerationSanctionType.SUSPENSION_7_DAYS: timedelta(days=7),
            ModerationSanctionType.SUSPENSION_30_DAYS: timedelta(days=30),
            ModerationSanctionType.PERMANENT_SUSPENSION: None,
        }
        now = timezone.now()
        changed = 0
        protected = 0

        with transaction.atomic():
            reports = (
                queryset
                .select_for_update()
                .select_related("reported_user")
            )

            for report in reports:
                user = report.reported_user

                if user.is_staff or user.is_superuser:
                    protected += 1
                    continue

                duration = durations[sanction_type]
                expires_at = (
                    now + duration
                    if duration is not None
                    else None
                )

                if sanction_type != ModerationSanctionType.WARNING:
                    user.is_suspended = True
                    user.suspension_until = expires_at
                    user.save(
                        update_fields=(
                            "is_suspended",
                            "suspension_until",
                            "updated_at",
                        )
                    )

                sanction = ModerationSanction.objects.create(
                    report=report,
                    user=user,
                    sanction_type=sanction_type,
                    moderator=request.user,
                    expires_at=expires_at,
                )

                notification_result = (
                    create_moderation_sanction_notification(
                        recipient=user,
                        sanction_id=sanction.id,
                        sanction_type=sanction_type,
                    )
                )

                if notification_result.created:
                    notification = notification_result.notification
                    transaction.on_commit(
                        lambda notification=notification: (
                            broadcast_notification_created(
                                notification=notification,
                                event_name="security.notification",
                            )
                        )
                    )

                changed += 1

        return changed, protected

    def _show_sanction_result(
        self,
        *,
        request,
        changed: int,
        protected: int,
        label: str,
    ) -> None:
        self.message_user(
            request,
            f"{changed} mesure(s) « {label} » enregistrée(s).",
        )
        if protected:
            self.message_user(
                request,
                (
                    f"{protected} compte(s) administratif(s) protégé(s) "
                    "ont été ignoré(s)."
                ),
                level=messages.WARNING,
            )

    @admin.action(description="Prendre en charge les dossiers sélectionnés")
    def mark_under_review(self, request, queryset) -> None:
        changed = self._transition_reports(
            request=request,
            queryset=queryset,
            destination=ReportStatus.UNDER_REVIEW,
        )
        self.message_user(
            request,
            f"{changed} dossier(s) placé(s) en cours d’examen.",
        )

    @admin.action(description="Marquer les dossiers sélectionnés comme traités")
    def mark_resolved(self, request, queryset) -> None:
        changed = self._transition_reports(
            request=request,
            queryset=queryset,
            destination=ReportStatus.RESOLVED,
        )
        self.message_user(
            request,
            f"{changed} dossier(s) marqué(s) comme traité(s).",
        )

    @admin.action(description="Classer les dossiers sélectionnés sans suite")
    def mark_rejected(self, request, queryset) -> None:
        changed = self._transition_reports(
            request=request,
            queryset=queryset,
            destination=ReportStatus.REJECTED,
        )
        self.message_user(
            request,
            f"{changed} dossier(s) classé(s) sans suite.",
        )

    @admin.action(description="Avertir les membres signalés sélectionnés")
    def warn_reported_users(self, request, queryset) -> None:
        changed, protected = self._sanction_reported_users(
            request=request,
            queryset=queryset,
            sanction_type=ModerationSanctionType.WARNING,
        )
        self._show_sanction_result(
            request=request,
            changed=changed,
            protected=protected,
            label="Avertissement",
        )

    @admin.action(description="Suspendre 7 jours les membres signalés")
    def suspend_reported_users_7_days(self, request, queryset) -> None:
        changed, protected = self._sanction_reported_users(
            request=request,
            queryset=queryset,
            sanction_type=ModerationSanctionType.SUSPENSION_7_DAYS,
        )
        self._show_sanction_result(
            request=request,
            changed=changed,
            protected=protected,
            label="Suspension de 7 jours",
        )

    @admin.action(description="Suspendre 30 jours les membres signalés")
    def suspend_reported_users_30_days(self, request, queryset) -> None:
        changed, protected = self._sanction_reported_users(
            request=request,
            queryset=queryset,
            sanction_type=ModerationSanctionType.SUSPENSION_30_DAYS,
        )
        self._show_sanction_result(
            request=request,
            changed=changed,
            protected=protected,
            label="Suspension de 30 jours",
        )

    @admin.action(description="Suspendre sans échéance les membres signalés")
    def suspend_reported_users_permanently(self, request, queryset) -> None:
        changed, protected = self._sanction_reported_users(
            request=request,
            queryset=queryset,
            sanction_type=ModerationSanctionType.PERMANENT_SUSPENSION,
        )
        self._show_sanction_result(
            request=request,
            changed=changed,
            protected=protected,
            label="Suspension sans échéance",
        )


@admin.register(ModerationSanction)
class ModerationSanctionAdmin(admin.ModelAdmin):
    """Journal de consultation en lecture seule des sanctions."""

    list_display = (
        "id",
        "sanction_type",
        "user_id",
        "report_id",
        "moderator_id",
        "expires_at",
        "created_at",
    )
    list_filter = (
        "sanction_type",
        "created_at",
        "expires_at",
    )
    search_fields = (
        "id",
        "user__id",
        "report__id",
        "moderator__id",
    )
    readonly_fields = (
        "id",
        "report",
        "user",
        "sanction_type",
        "moderator",
        "internal_note",
        "expires_at",
        "created_at",
    )
    ordering = ("-created_at",)
    list_select_related = ("report", "user", "moderator")

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(SanctionAppeal)
class SanctionAppealAdmin(admin.ModelAdmin):
    """
    File de révision des contestations.

    Le texte du membre est consultable, mais la sanction et l'identité du
    membre restent immuables. Les actions de masse enregistrent toujours le
    modérateur et la date de décision.
    """

    list_display = (
        "id",
        "user_id",
        "status",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = ("id", "user__id", "sanction__id")
    readonly_fields = (
        "id",
        "sanction",
        "user",
        "message",
        "status",
        "reviewed_by",
        "created_at",
        "reviewed_at",
    )
    actions = ("accept_appeals", "reject_appeals")
    ordering = ("-created_at",)
    list_select_related = ("user", "sanction", "reviewed_by")

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def _review(self, *, request, queryset, destination: str) -> int:
        changed = 0
        with transaction.atomic():
            for appeal in queryset.select_for_update().select_related("user"):
                if appeal.status != SanctionAppealStatus.PENDING:
                    continue

                appeal.status = destination
                appeal.reviewed_by = request.user
                appeal.reviewed_at = timezone.now()
                appeal.save(
                    update_fields=("status", "reviewed_by", "reviewed_at")
                )

                if destination == SanctionAppealStatus.ACCEPTED:
                    appeal.user.is_suspended = False
                    appeal.user.suspension_until = None
                    appeal.user.save(
                        update_fields=(
                            "is_suspended",
                            "suspension_until",
                            "updated_at",
                        )
                    )
                changed += 1
        return changed

    @admin.action(description="Accepter les contestations sélectionnées")
    def accept_appeals(self, request, queryset) -> None:
        changed = self._review(
            request=request,
            queryset=queryset,
            destination=SanctionAppealStatus.ACCEPTED,
        )
        self.message_user(
            request,
            f"{changed} contestation(s) acceptée(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Refuser les contestations sélectionnées")
    def reject_appeals(self, request, queryset) -> None:
        changed = self._review(
            request=request,
            queryset=queryset,
            destination=SanctionAppealStatus.REJECTED,
        )
        self.message_user(
            request,
            f"{changed} contestation(s) refusée(s).",
            level=messages.WARNING,
        )
