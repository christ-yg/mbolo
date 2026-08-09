from django.urls import path

from .views import (
    CSRFTokenView,
    HealthCheckView,
    LivenessCheckView,
    ReadinessCheckView,
)

app_name = "core"

urlpatterns = [
    path("csrf/", CSRFTokenView.as_view(), name="csrf-token"),
    # Route historique conservée pour les clients existants.
    path("health/", HealthCheckView.as_view(), name="health"),
    path("health/live/", LivenessCheckView.as_view(), name="health-live"),
    path("health/ready/", ReadinessCheckView.as_view(), name="health-ready"),
]
