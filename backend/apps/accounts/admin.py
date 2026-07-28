from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    AccountSecurityEvent,
    AccountSession,
    LoginActivity,
    User,
)


@admin.register(User)
class MboloUserAdmin(UserAdmin):
    """
    Administration sécurisée des comptes Mbolo.

    Les actions de masse protègent systématiquement les comptes staff et
    superutilisateurs. Les mots de passe ne sont jamais visibles.
    """

    ordering = ("-created_at",)
    list_display = (
        "email",
        "account_state",
        "email_state",
        "staff_state",
        "created_at",
        "last_login",
    )
    list_filter = (
        "is_active",
        "is_suspended",
        "is_email_verified",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    search_fields = ("email", "id")
    readonly_fields = (
        "id",
        "last_login",
        "date_joined",
        "created_at",
        "updated_at",
        "terms_accepted_at",
        "terms_version",
        "privacy_version",
    )
    fieldsets = (
        (
            "Identité du compte",
            {"fields": ("id", "email", "password")},
        ),
        (
            "État du compte",
            {
                "fields": (
                    "is_active",
                    "is_suspended",
                    "suspension_until",
                    "is_email_verified",
                    "is_phone_verified",
                )
            },
        ),
        (
            "Sécurité",
            {
                "fields": (
                    "email_2fa_enabled",
                    "login_alert_emails_enabled",
                )
            },
        ),
        (
            "Autorisations administratives",
            {
                "classes": ("collapse",),
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Consentements et dates",
            {
                "classes": ("collapse",),
                "fields": (
                    "terms_accepted_at",
                    "terms_version",
                    "privacy_version",
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            "Créer un compte",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    actions = (
        "suspend_7_days",
        "suspend_30_days",
        "suspend_permanently",
        "reactivate_accounts",
        "revoke_known_sessions",
    )

    @admin.display(description="Compte", ordering="is_suspended")
    def account_state(self, user):
        if not user.is_active:
            return format_html(
                '<span class="mbolo-status mbolo-status--rejected">Désactivé</span>'
            )
        if user.is_suspended:
            label = "Suspendu"
            if user.suspension_until:
                label = f"Suspendu jusqu’au {user.suspension_until:%d/%m/%Y}"
            return format_html(
                '<span class="mbolo-status mbolo-status--pending">{}</span>',
                label,
            )
        return format_html(
            '<span class="mbolo-status mbolo-status--approved">Actif</span>'
        )

    @admin.display(description="E-mail", ordering="is_email_verified")
    def email_state(self, user):
        css = "approved" if user.is_email_verified else "neutral"
        label = "Vérifié" if user.is_email_verified else "Non vérifié"
        return format_html(
            '<span class="mbolo-status mbolo-status--{}">{}</span>',
            css,
            label,
        )

    @admin.display(description="Privilèges", ordering="is_staff")
    def staff_state(self, user):
        if user.is_superuser:
            return "Superutilisateur"
        if user.is_staff:
            return "Staff"
        return "Membre"

    def _suspend(self, request, queryset, *, days=None):
        now = timezone.now()
        changed = 0
        protected = 0

        with transaction.atomic():
            for user in queryset.select_for_update():
                if user.is_staff or user.is_superuser:
                    protected += 1
                    continue
                user.is_suspended = True
                user.suspension_until = (
                    now + timezone.timedelta(days=days)
                    if days is not None
                    else None
                )
                user.save(
                    update_fields=(
                        "is_suspended",
                        "suspension_until",
                        "updated_at",
                    )
                )
                user.account_sessions.all().delete()
                changed += 1

        self.message_user(
            request,
            f"{changed} compte(s) suspendu(s). "
            f"{protected} compte(s) privilégié(s) protégé(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Suspendre pendant 7 jours")
    def suspend_7_days(self, request, queryset):
        self._suspend(request, queryset, days=7)

    @admin.action(description="Suspendre pendant 30 jours")
    def suspend_30_days(self, request, queryset):
        self._suspend(request, queryset, days=30)

    @admin.action(description="Suspendre sans échéance")
    def suspend_permanently(self, request, queryset):
        self._suspend(request, queryset)

    @admin.action(description="Réactiver les comptes sélectionnés")
    def reactivate_accounts(self, request, queryset):
        protected_queryset = queryset.filter(
            is_staff=False,
            is_superuser=False,
        )
        changed = protected_queryset.update(
            is_active=True,
            is_suspended=False,
            suspension_until=None,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{changed} compte(s) réactivé(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Révoquer toutes les sessions connues")
    def revoke_known_sessions(self, request, queryset):
        user_ids = list(queryset.values_list("id", flat=True))
        deleted, _details = AccountSession.objects.filter(
            user_id__in=user_ids
        ).delete()
        self.message_user(
            request,
            f"{deleted} session(s) connue(s) supprimée(s).",
            level=messages.WARNING,
        )


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "method", "device", "ip_fingerprint", "created_at")
    list_filter = ("method", "created_at")
    search_fields = ("user__email", "user__id", "device", "ip_fingerprint")
    readonly_fields = (
        "id",
        "user",
        "method",
        "device",
        "ip_fingerprint",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AccountSecurityEvent)
class AccountSecurityEventAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "outcome", "reason", "created_at")
    list_filter = ("event", "outcome", "created_at")
    search_fields = ("user__email", "user__id", "event", "reason")
    readonly_fields = ("id", "user", "event", "outcome", "reason", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AccountSession)
class AccountSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "device", "ip_fingerprint", "created_at", "last_seen_at")
    list_filter = ("created_at", "last_seen_at")
    search_fields = ("user__email", "user__id", "device", "ip_fingerprint")
    readonly_fields = (
        "id",
        "user",
        "session_key_hash",
        "device",
        "ip_fingerprint",
        "created_at",
        "last_seen_at",
    )

    def has_add_permission(self, request):
        return False
