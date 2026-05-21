"""Unit tests for the Transaction model."""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from apps.accounts.models import Account
from apps.transactions.models import Transaction

class TransactionModelTest(TestCase):
    """Tests for Transaction model fields and basic behavior."""

    def setUp(self) -> None:
        self.user_a = User.objects.create_user(username="user_a", email="a@test.com", password="password")
        self.user_b = User.objects.create_user(username="user_b", email="b@test.com", password="password")
        self.acc_a = Account.objects.create(owner=self.user_a, balance=Decimal("100"), currency="USD")
        self.acc_b = Account.objects.create(owner=self.user_b, balance=Decimal("100"), currency="USD")

    def test_create_transaction_success(self) -> None:
        txn = Transaction.objects.create(
            from_account=self.acc_a,
            to_account=self.acc_b,
            amount=Decimal("50.00"),
            currency="USD",
            status=Transaction.Status.COMPLETED,
            idempotency_key="unique-key-1"
        )
        self.assertEqual(txn.status, Transaction.Status.COMPLETED)
        self.assertEqual(txn.amount, Decimal("50.00"))
        self.assertEqual(txn.idempotency_key, "unique-key-1")

    def test_str_representation(self) -> None:
        txn = Transaction.objects.create(
            from_account=self.acc_a,
            to_account=self.acc_b,
            amount=Decimal("50.00"),
            currency="USD",
            idempotency_key="unique-key-2"
        )
        self.assertIn("USD", str(txn))
        self.assertIn("50.00", str(txn))
