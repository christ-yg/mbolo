from django.urls import path

from .views import (
    PaymentCancelView,
    PaymentCheckoutView,
    PaymentConfirmTestView,
    PaymentHistoryView,
    ProfileBoostView,
    PremiumOverviewView,
    PremiumPrivacyView,
)


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
    path(
        "payments/checkout/",
        PaymentCheckoutView.as_view(),
        name="premium-payment-checkout",
    ),
    path(
        "payments/confirm-test/",
        PaymentConfirmTestView.as_view(),
        name="premium-payment-confirm-test",
    ),
    path(
        "payments/cancel/",
        PaymentCancelView.as_view(),
        name="premium-payment-cancel",
    ),
    path(
        "payments/history/",
        PaymentHistoryView.as_view(),
        name="premium-payment-history",
    ),
]
