from django.urls import path

from .views import PremiumOverviewView, PremiumPrivacyView


app_name = "subscriptions"

urlpatterns = [
    path(
        "overview/",
        PremiumOverviewView.as_view(),
        name="premium-overview",
    ),
    path(
        "privacy/",
        PremiumPrivacyView.as_view(),
        name="premium-privacy",
    ),
]
