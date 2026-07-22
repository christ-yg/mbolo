"""
Routes du module de sécurité communautaire.

Préfixe défini dans config/urls.py :

    /api/v1/safety/
"""

from django.urls import path

from .report_views import ReportListCreateView
from .views import (
    BlockDeleteView,
    BlockListCreateView,
    ProfileBlockCreateView,
    ProfileReportCreateView,
)


app_name = "safety"


urlpatterns = [
    # ---------------------------------------------------------
    # Blocages
    # ---------------------------------------------------------
    path(
        "blocks/",
        BlockListCreateView.as_view(),
        name="block-list-create",
    ),
    path(
        "blocks/<uuid:block_id>/",
        BlockDeleteView.as_view(),
        name="block-delete",
    ),

    # ---------------------------------------------------------
    # Signalements
    # ---------------------------------------------------------
    path(
        "reports/",
        ReportListCreateView.as_view(),
        name="report-list-create",
    ),
    path(
        "profiles/<uuid:profile_id>/block/",
        ProfileBlockCreateView.as_view(),
        name="profile-block-create",
    ),
    path(
        "profiles/<uuid:profile_id>/report/",
        ProfileReportCreateView.as_view(),
        name="profile-report-create",
    ),
]
