from datetime import timedelta

from django import template
from django.contrib.admin.models import LogEntry
from django.utils import timezone

from apps.accounts.models import User
from apps.photos.models import ProfilePhoto
from apps.profiles.models import ProfileVerification
from apps.safety.models import Report, ReportStatus, SanctionAppeal, SanctionAppealStatus
from apps.subscriptions.models import PaymentStatus, PaymentTransaction, Subscription

register = template.Library()


@register.inclusion_tag(
    "admin/includes/mbolo_dashboard.html",
    takes_context=True,
)
def mbolo_admin_dashboard(context):
    """
    Statistiques opérationnelles minimales du centre de pilotage.

    Elles sont calculées uniquement lors de l'affichage de l'accueil admin.
    Aucun secret d'authentification ni contenu privé de message n'est exposé.
    """

    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_30d = now - timedelta(days=30)

    successful_revenue = PaymentTransaction.objects.filter(
        status=PaymentStatus.SUCCEEDED,
        verified_at__gte=last_30d,
    )

    return {
        "request": context.get("request"),
        "stats": {
            "members": User.objects.filter(is_staff=False).count(),
            "new_members_24h": User.objects.filter(
                is_staff=False,
                created_at__gte=last_24h,
            ).count(),
            "suspended": User.objects.filter(
                is_staff=False,
                is_suspended=True,
            ).count(),
            "pending_reports": Report.objects.filter(
                status__in=(
                    ReportStatus.PENDING,
                    ReportStatus.UNDER_REVIEW,
                )
            ).count(),
            "pending_verifications": ProfileVerification.objects.filter(
                status=ProfileVerification.Status.PENDING
            ).count(),
            "pending_photos": ProfilePhoto.objects.filter(
                moderation_status=ProfilePhoto.ModerationStatus.PENDING
            ).count(),
            "pending_appeals": SanctionAppeal.objects.filter(
                status=SanctionAppealStatus.PENDING
            ).count(),
            "active_subscriptions": Subscription.objects.filter(
                status__in=("active", "trial"),
            ).count(),
            "successful_payments_30d": successful_revenue.count(),
            "revenue_30d": sum(
                successful_revenue.values_list("amount_xaf", flat=True)
            ),
        },
        "recent_actions": LogEntry.objects.select_related(
            "user",
            "content_type",
        )[:8],
    }
