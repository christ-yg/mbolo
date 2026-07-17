from django.urls import path

from .views import (
    CurrentUserView,
    EmailVerificationConfirmView,
    EmailVerificationRequestView,
    LoginView,
    LogoutView,
    RegisterView,
)


app_name = "accounts"

urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
    path(
        "email-verification/request/",
        EmailVerificationRequestView.as_view(),
        name="email-verification-request",
    ),
    path(
        "email-verification/confirm/",
        EmailVerificationConfirmView.as_view(),
        name="email-verification-confirm",
    ),
]
