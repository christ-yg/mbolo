import base64

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from apps.notifications.models import Notification

from .models import (
    Profile,
    ProfileVerification,
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


@admin.register(ProfileVerification)
class ProfileVerificationAdmin(admin.ModelAdmin):
    """
    File de revue réservée aux administrateurs Django.

    Le selfie privé est lu par le serveur puis affiché uniquement dans
    l'administration authentifiée. Aucun chemin public n'est créé.
    """

    list_display = (
        "id",
        "profile",
        "status",
        "submitted_at",
        "reviewed_at",
    )
    list_filter = ("status", "submitted_at", "reviewed_at")
    readonly_fields = (
        "id",
        "profile",
        "selfie_preview",
        "submitted_at",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    fields = (
        "id",
        "profile",
        "status",
        "selfie_preview",
        "rejection_reason",
        "submitted_at",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    actions = ("approve_requests", "reject_requests")

    @admin.display(description="Selfie privé")
    def selfie_preview(self, verification):
        if not verification.selfie:
            return "Aucun selfie"

        try:
            verification.selfie.open("rb")
            encoded = base64.b64encode(
                verification.selfie.read()
            ).decode("ascii")
        finally:
            verification.selfie.close()

        return format_html(
            '<img src="data:image/webp;base64,{}" '
            'style="max-width:420px;max-height:520px;object-fit:contain" '
            'alt="Selfie privé de vérification">',
            encoded,
        )

    @staticmethod
    def _notify(verification, approved: bool) -> None:
        Notification.objects.update_or_create(
            recipient=verification.profile.user,
            source_key=f"profile-verification:{verification.id}",
            defaults={
                "kind": Notification.Kind.SYSTEM,
                "title": (
                    "Ton profil est maintenant vérifié"
                    if approved
                    else "Ta vérification doit être recommencée"
                ),
                "body": (
                    "Le badge Profil vérifié est désormais visible."
                    if approved
                    else verification.rejection_reason
                ),
                "target_path": "/profile/verification",
                "metadata": {
                    "verification_status": verification.status,
                },
            },
        )

    @admin.action(description="Approuver les demandes sélectionnées")
    def approve_requests(self, request, queryset):
        reviewed = 0
        for verification in queryset.select_related("profile__user"):
            if verification.status != ProfileVerification.Status.PENDING:
                continue
            verification.status = ProfileVerification.Status.APPROVED
            verification.rejection_reason = ""
            verification.reviewed_at = timezone.now()
            verification.save()
            self._notify(verification, approved=True)
            reviewed += 1
        self.message_user(
            request,
            f"{reviewed} demande(s) approuvée(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Refuser : selfie insuffisant ou non conforme")
    def reject_requests(self, request, queryset):
        reviewed = 0
        for verification in queryset.select_related("profile__user"):
            if verification.status != ProfileVerification.Status.PENDING:
                continue
            verification.status = ProfileVerification.Status.REJECTED
            verification.rejection_reason = (
                "Le selfie n'est pas assez net ou ne permet pas de "
                "confirmer la correspondance avec la photo principale."
            )
            verification.reviewed_at = timezone.now()
            verification.save()
            self._notify(verification, approved=False)
            reviewed += 1
        self.message_user(
            request,
            f"{reviewed} demande(s) refusée(s).",
            level=messages.WARNING,
        )
