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
        "member",
        "status_badge",
        "submitted_at",
        "reviewed_at",
    )
    list_filter = ("status", "submitted_at", "reviewed_at")
    search_fields = (
        "profile__display_name",
        "profile__user__email",
    )
    list_select_related = ("profile", "profile__user")
    ordering = ("-submitted_at",)
    date_hierarchy = "submitted_at"
    list_per_page = 30
    readonly_fields = (
        "id",
        "profile",
        "comparison_preview",
        "submitted_at",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    fields = (
        "id",
        "profile",
        "status",
        "comparison_preview",
        "rejection_reason",
        "submitted_at",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    actions = ("approve_requests", "reject_requests")

    @admin.display(description="Membre", ordering="profile__display_name")
    def member(self, verification):
        return format_html(
            "<strong>{}</strong><br><small>{}</small>",
            verification.profile.display_name or "Profil sans nom",
            verification.profile.user.email,
        )

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, verification):
        labels = {
            ProfileVerification.Status.NOT_SUBMITTED: ("Non demandée", "neutral"),
            ProfileVerification.Status.PENDING: ("En attente", "pending"),
            ProfileVerification.Status.APPROVED: ("Approuvée", "approved"),
            ProfileVerification.Status.REJECTED: ("Refusée", "rejected"),
        }
        label, css_class = labels.get(
            verification.status,
            (verification.status, "neutral"),
        )
        return format_html(
            '<span class="mbolo-status mbolo-status--{}">{}</span>',
            css_class,
            label,
        )

    @staticmethod
    def _private_image_data_uri(image_field):
        """Lit une image côté serveur sans créer d'URL publique."""
        if not image_field:
            return ""
        try:
            image_field.open("rb")
            encoded = base64.b64encode(
                image_field.read()
            ).decode("ascii")
        except (FileNotFoundError, OSError, ValueError):
            return ""
        finally:
            try:
                image_field.close()
            except (AttributeError, ValueError):
                pass
        return f"data:image/webp;base64,{encoded}"

    @admin.display(description="Comparaison humaine sécurisée")
    def comparison_preview(self, verification):
        selfie_uri = self._private_image_data_uri(verification.selfie)
        primary = verification.profile.photos.filter(
            is_primary=True,
        ).first()
        primary_uri = self._private_image_data_uri(
            primary.image if primary else None
        )

        if not selfie_uri:
            return "Le selfie privé est introuvable."

        return format_html(
            '<div class="mbolo-comparison">'
            '<figure><figcaption>Photo principale</figcaption>{}</figure>'
            '<figure><figcaption>Selfie privé envoyé</figcaption>'
            '<img src="{}" alt="Selfie privé de vérification"></figure>'
            "</div>",
            (
                format_html(
                    '<img src="{}" alt="Photo principale du profil">',
                    primary_uri,
                )
                if primary_uri
                else format_html(
                    '<div class="mbolo-image-missing">'
                    "Aucune photo principale disponible</div>"
                )
            ),
            selfie_uri,
        )

    class Media:
        css = {
            "all": ("admin/css/mbolo_admin.css",),
        }

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
