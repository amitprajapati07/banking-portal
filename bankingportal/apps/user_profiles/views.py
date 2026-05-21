"""Views for authentication and user profile management."""

import logging

from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.utils import get_client_ip

from apps.user_profiles.models import UserProfile
from apps.user_profiles.serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UpdateUserProfileSerializer,
    UserDetailSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth — Register
# ---------------------------------------------------------------------------


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/

    Creates a new user account.  The ``UserProfile`` is created automatically
    via the ``post_save`` signal.  Returns the new user's detail payload.
    """

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = serializer.save()

        logger.info("New user registered: pk=%s username=%s", user.pk, user.username)

        detail_serializer = UserDetailSerializer(
            user, context={"request": request}
        )
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Auth — Login (JWT)
# ---------------------------------------------------------------------------


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/

    Returns ``access`` and ``refresh`` JWT tokens.
    Extends SimpleJWT's TokenObtainPairView and records the client IP.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        response: Response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            # Persist last login IP (best-effort).
            try:
                user: User = User.objects.get(
                    username=request.data.get("username", "")
                )
                user.profile.last_login_ip = get_client_ip(request)
                user.profile.save(update_fields=["last_login_ip", "updated_at"])
            except (User.DoesNotExist, UserProfile.DoesNotExist):
                pass
        return response


# ---------------------------------------------------------------------------
# Auth — Logout
# ---------------------------------------------------------------------------


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Blacklists the provided ``refresh`` token so it can no longer be used
    to obtain new access tokens.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RegisterSerializer

    def post(self, request: Request) -> Response:
        refresh_token: str | None = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "MISSING_FIELD", "detail": "refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            return Response(
                {"error": "INVALID_TOKEN", "detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# User — Me
# ---------------------------------------------------------------------------


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/users/me/ — Return the authenticated user's full profile.
    PATCH /api/v1/users/me/ — Update mutable profile fields.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self) -> UserProfile:
        user = self.request.user
        if user.is_anonymous:
            return UserProfile.objects.none()
        return user.profile

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UpdateUserProfileSerializer
        return UserDetailSerializer

    def get_serializer(self, *args, **kwargs):
        # For GET we serialise the User, for PATCH we serialise the Profile.
        if self.request.method in ("PUT", "PATCH"):
            kwargs["instance"] = self.request.user.profile
            return UpdateUserProfileSerializer(
                *args, **kwargs, context={"request": self.request}
            )
        return UserDetailSerializer(
            self.request.user,
            context={"request": self.request},
        )

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer()
        return Response(serializer.data)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        serializer = UpdateUserProfileSerializer(
            request.user.profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            UserDetailSerializer(
                request.user, context={"request": request}
            ).data
        )


# ---------------------------------------------------------------------------
# User — Change password
# ---------------------------------------------------------------------------


class ChangePasswordView(APIView):
    """
    POST /api/v1/users/me/change-password/

    Validates the old password, applies Django's password validators to the
    new one, and updates the user's password.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        logger.info("Password changed for user pk=%s", user.pk)

        return Response(
            {"detail": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )
