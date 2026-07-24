from django.urls import path

from .views import ProfileBoostView, PremiumOverviewView, PremiumPrivacyView


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
    path(
        "boost/",
        ProfileBoostView.as_view(),
        name="premium-boost",
    ),
]
