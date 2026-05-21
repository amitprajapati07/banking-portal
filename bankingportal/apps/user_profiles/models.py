"""UserProfile model — extends Django's built-in User with KYC data."""

import uuid

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    One-to-one extension of Django's built-in ``User`` model.

    Created automatically via a ``post_save`` signal whenever a new
    ``User`` instance is saved.
    """

    class KYCStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    # ------------------------------------------------------------------ #
    # Fields
    # ------------------------------------------------------------------ #
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    phone_number = models.CharField(
        max_length=20, unique=True, null=True, blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    is_verified = models.BooleanField(default=False)
    kyc_status = models.CharField(
        max_length=10,
        choices=KYCStatus.choices,
        default=KYCStatus.PENDING,
        db_index=True,
    )
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------ #
    # Meta
    # ------------------------------------------------------------------ #
    class Meta:
        db_table = "user_profiles"
        ordering = ["-created_at"]
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    # ------------------------------------------------------------------ #
    # Dunder
    # ------------------------------------------------------------------ #
    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} <{self.user.email}>"

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def full_name(self) -> str:
        """Return the user's full name (display convenience)."""
        return self.user.get_full_name()

    @property
    def can_transact(self) -> bool:
        """
        True only when:
          - The underlying Django user account is active.
          - The KYC status is ``VERIFIED``.
        """
        return (
            self.user.is_active
            and self.kyc_status == self.KYCStatus.VERIFIED
        )