"""Unit tests for the UserProfile model."""

from django.contrib.auth.models import User
from django.test import TestCase

from apps.user_profiles.models import UserProfile


class UserProfileModelTest(TestCase):
    """Tests for UserProfile model behaviour and properties."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="User",
        )
        self.profile: UserProfile = self.user.profile

    # ------------------------------------------------------------------
    # Signal creates profile automatically
    # ------------------------------------------------------------------

    def test_profile_auto_created_on_user_creation(self) -> None:
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)

    def test_profile_kyc_status_defaults_to_pending(self) -> None:
        self.assertEqual(self.profile.kyc_status, UserProfile.KYCStatus.PENDING)

    def test_profile_is_verified_defaults_to_false(self) -> None:
        self.assertFalse(self.profile.is_verified)

    # ------------------------------------------------------------------
    # can_transact property
    # ------------------------------------------------------------------

    def test_can_transact_false_when_kyc_pending(self) -> None:
        self.assertFalse(self.profile.can_transact)

    def test_can_transact_false_when_user_inactive(self) -> None:
        self.profile.kyc_status = UserProfile.KYCStatus.VERIFIED
        self.profile.save()
        self.user.is_active = False
        self.user.save()
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.can_transact)

    def test_can_transact_true_when_active_and_verified(self) -> None:
        self.profile.kyc_status = UserProfile.KYCStatus.VERIFIED
        self.profile.save()
        self.assertTrue(self.profile.can_transact)

    # ------------------------------------------------------------------
    # __str__
    # ------------------------------------------------------------------

    def test_str_representation(self) -> None:
        expected = f"Test User <{self.user.email}>"
        self.assertEqual(str(self.profile), expected)
