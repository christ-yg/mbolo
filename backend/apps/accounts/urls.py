from django.urls import path

from .views import (
    ActivityHeartbeatView,
    ChangePasswordView,
    CurrentUserView,
    EmailVerificationConfirmView,
    EmailVerificationRequestView,
    DeactivateAccountView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RevokeOtherSessionsView,
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
        "activity/",
        ActivityHeartbeatView.as_view(),
        name="activity-heartbeat",
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
    path(
        "password-reset/request/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "security/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "security/revoke-sessions/",
        RevokeOtherSessionsView.as_view(),
        name="revoke-other-sessions",
    ),
    path(
        "security/deactivate/",
        DeactivateAccountView.as_view(),
        name="deactivate-account",
    ),
]
