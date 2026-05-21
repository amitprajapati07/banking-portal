"""URL patterns for auth and user-profile endpoints."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.user_profiles.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

urlpatterns = [
    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    # ------------------------------------------------------------------
    # User self-service
    # ------------------------------------------------------------------
    path("users/me/", MeView.as_view(), name="users-me"),
    path(
        "users/me/change-password/",
        ChangePasswordView.as_view(),
        name="users-change-password",
    ),
]
