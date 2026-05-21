"""Unit tests for the Account model."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import Account


def _make_user(username: str = "bob", password: str = "SecurePass123!") -> User:
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )


class AccountModelTest(TestCase):
    """Tests for Account model fields, defaults, and constraints."""

    def setUp(self) -> None:
        self.user = _make_user()

    def test_create_account_defaults(self) -> None:
        acc = Account.objects.create(
            owner=self.user,
            currency="USD",
            balance=Decimal("100.0000"),
        )
        self.assertEqual(acc.status, Account.Status.ACTIVE)
        self.assertEqual(acc.currency, "USD")
        self.assertEqual(acc.balance, Decimal("100.0000"))

    def test_uuid_primary_key(self) -> None:
        acc = Account.objects.create(
            owner=self.user, currency="EUR", balance=Decimal("0")
        )
        self.assertIsNotNone(acc.id)
        self.assertEqual(len(str(acc.id)), 36)  # UUID canonical form

    def test_balance_is_decimal_not_float(self) -> None:
        acc = Account.objects.create(
            owner=self.user, currency="USD", balance=Decimal("10.1234")
        )
        acc.refresh_from_db()
        self.assertIsInstance(acc.balance, Decimal)
        self.assertEqual(acc.balance, Decimal("10.1234"))

    def test_str_representation(self) -> None:
        acc = Account.objects.create(
            owner=self.user, currency="USD", balance=Decimal("0")
        )
        self.assertIn("USD", str(acc))
        self.assertIn(self.user.username, str(acc))

    def test_status_choices(self) -> None:
        choices = {s.value for s in Account.Status}
        self.assertEqual(choices, {"ACTIVE", "FROZEN", "CLOSED"})
