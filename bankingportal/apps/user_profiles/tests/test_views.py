"""Integration tests for auth and user-profile API endpoints."""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.user_profiles.models import UserProfile


def _create_user(
    username: str = "alice",
    email: str = "alice@example.com",
    password: str = "SecurePass123!",
) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Alice",
        last_name="Smith",
    )


def _get_tokens(client: APIClient, username: str, password: str) -> dict:
    response = client.post(
        reverse("auth-login"),
        {"username": username, "password": password},
        format="json",
    )
    return response.data


class RegisterViewTest(APITestCase):
    """Tests for POST /api/v1/auth/register/."""

    def test_register_success(self) -> None:
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(
            reverse("auth-register"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("profile", response.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_duplicate_email(self) -> None:
        _create_user(email="dup@example.com")
        payload = {
            "username": "dup2",
            "email": "dup@example.com",
            "first_name": "Dup",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(
            reverse("auth-register"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self) -> None:
        payload = {
            "username": "mismatch",
            "email": "mismatch@example.com",
            "first_name": "X",
            "last_name": "Y",
            "password": "SecurePass123!",
            "password_confirm": "WrongPass123!",
        }
        response = self.client.post(
            reverse("auth-register"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(APITestCase):
    """Tests for POST /api/v1/auth/login/."""

    def setUp(self) -> None:
        self.user = _create_user()

    def test_login_success(self) -> None:
        response = self.client.post(
            reverse("auth-login"),
            {"username": "alice", "password": "SecurePass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self) -> None:
        response = self.client.post(
            reverse("auth-login"),
            {"username": "alice", "password": "WrongPass!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTest(APITestCase):
    """Tests for GET/PATCH /api/v1/users/me/."""

    def setUp(self) -> None:
        self.user = _create_user()
        tokens = _get_tokens(self.client, "alice", "SecurePass123!")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
        )

    def test_get_profile_authenticated(self) -> None:
        response = self.client.get(reverse("users-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")
        self.assertIn("profile", response.data)

    def test_get_profile_unauthenticated(self) -> None:
        self.client.credentials()  # remove auth header
        response = self.client.get(reverse("users-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile(self) -> None:
        response = self.client.patch(
            reverse("users-me"),
            {"phone_number": "+15550001111"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, "+15550001111")


class ChangePasswordViewTest(APITestCase):
    """Tests for POST /api/v1/users/me/change-password/."""

    def setUp(self) -> None:
        self.user = _create_user()
        tokens = _get_tokens(self.client, "alice", "SecurePass123!")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
        )

    def test_change_password_success(self) -> None:
        response = self.client.post(
            reverse("users-change-password"),
            {
                "old_password": "SecurePass123!",
                "new_password": "NewSecurePass456!",
                "new_password_confirm": "NewSecurePass456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecurePass456!"))

    def test_change_password_wrong_old(self) -> None:
        response = self.client.post(
            reverse("users-change-password"),
            {
                "old_password": "WrongOldPass!",
                "new_password": "NewSecurePass456!",
                "new_password_confirm": "NewSecurePass456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
