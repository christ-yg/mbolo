from unittest.mock import patch
from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.notifications.models import Notification

from .admin import ReportAdmin
from .models import (
    ModerationSanction,
    ModerationSanctionType,
    Report,
    ReportReason,
    ReportStatus,
)


User = get_user_model()


class ReportAdminWorkflowTests(TestCase):
    """
    Vérifie que les raccourcis de modération conservent la traçabilité.
    """

    def setUp(self) -> None:
        self.reporter = User.objects.create_user(
            email="admin-report-reporter@example.com",
            password="Strong-Test-Password-2026!",
        )
        self.target = User.objects.create_user(
            email="admin-report-target@example.com",
            password="Strong-Test-Password-2026!",
        )
        self.moderator = User.objects.create_superuser(
            email="admin-report-moderator@example.com",
            password="Strong-Admin-Password-2026!",
        )
        self.report = Report.objects.create(
            reporter=self.reporter,
            reported_user=self.target,
            reason=ReportReason.HARASSMENT,
            description="Description utile à la modération.",
        )
        self.admin = ReportAdmin(Report, AdminSite())
        self.request = RequestFactory().post("/admin/safety/report/")
        self.request.user = self.moderator

    @patch.object(ReportAdmin, "message_user")
    def test_take_ownership_records_moderator(self, _message_user) -> None:
        self.admin.mark_under_review(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.UNDER_REVIEW)
        self.assertEqual(self.report.reviewed_by, self.moderator)
        self.assertIsNone(self.report.resolved_at)
        notification = Notification.objects.get(
            recipient=self.reporter,
            source_key=(
                f"report:{self.report.id}:"
                f"{ReportStatus.UNDER_REVIEW}"
            ),
        )
        self.assertEqual(notification.kind, Notification.Kind.SYSTEM)
        self.assertEqual(notification.target_path, "/reports")
        self.assertNotIn(
            self.moderator.email,
            f"{notification.title} {notification.body}",
        )
        self.assertNotIn(
            self.report.description,
            f"{notification.title} {notification.body}",
        )

    @patch.object(ReportAdmin, "message_user")
    def test_resolve_sets_timestamp_and_moderator(self, _message_user) -> None:
        self.admin.mark_resolved(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.RESOLVED)
        self.assertEqual(self.report.reviewed_by, self.moderator)
        self.assertIsNotNone(self.report.resolved_at)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.reporter,
                source_key=(
                    f"report:{self.report.id}:"
                    f"{ReportStatus.RESOLVED}"
                ),
            ).exists()
        )

    @patch.object(ReportAdmin, "message_user")
    def test_finalized_report_is_not_reopened(self, _message_user) -> None:
        self.admin.mark_rejected(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )
        resolved_at = Report.objects.get(pk=self.report.pk).resolved_at

        self.admin.mark_under_review(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.REJECTED)
        self.assertEqual(self.report.resolved_at, resolved_at)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.reporter,
                source_key__startswith=f"report:{self.report.id}:",
            ).count(),
            1,
        )

    @patch.object(ReportAdmin, "message_user")
    def test_warning_is_logged_without_suspension(self, _message_user) -> None:
        self.admin.warn_reported_users(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )

        self.target.refresh_from_db()
        sanction = ModerationSanction.objects.get(
            report=self.report,
            user=self.target,
        )

        self.assertEqual(
            sanction.sanction_type,
            ModerationSanctionType.WARNING,
        )
        self.assertFalse(self.target.is_suspended)
        self.assertIsNone(self.target.suspension_until)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.target,
                source_key=f"moderation-sanction:{sanction.id}",
            ).exists()
        )

    @patch.object(ReportAdmin, "message_user")
    def test_temporary_suspension_has_expiration(self, _message_user) -> None:
        before = timezone.now()

        self.admin.suspend_reported_users_7_days(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )

        self.target.refresh_from_db()
        sanction = ModerationSanction.objects.get(report=self.report)

        self.assertTrue(self.target.is_suspended)
        self.assertIsNotNone(self.target.suspension_until)
        self.assertGreater(
            self.target.suspension_until,
            before + timedelta(days=6),
        )
        self.assertEqual(
            sanction.expires_at,
            self.target.suspension_until,
        )

    @patch.object(ReportAdmin, "message_user")
    def test_permanent_suspension_has_no_expiration(self, _message_user) -> None:
        self.admin.suspend_reported_users_permanently(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )

        self.target.refresh_from_db()
        self.assertTrue(self.target.is_suspended)
        self.assertIsNone(self.target.suspension_until)

    @patch.object(ReportAdmin, "message_user")
    def test_staff_target_is_protected(self, _message_user) -> None:
        self.target.is_staff = True
        self.target.save(update_fields=("is_staff",))

        self.admin.suspend_reported_users_permanently(
            self.request,
            Report.objects.filter(pk=self.report.pk),
        )

        self.target.refresh_from_db()
        self.assertFalse(self.target.is_suspended)
        self.assertFalse(
            ModerationSanction.objects.filter(
                report=self.report,
            ).exists()
        )
