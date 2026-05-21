"""Integration tests for Transaction API endpoints and Transfer Service."""

from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.accounts.models import Account
from apps.transactions.models import Transaction
from apps.user_profiles.models import UserProfile

class TransactionViewTest(APITestCase):
    """Integration tests for the transfer flow and transaction history."""

    def setUp(self) -> None:
        # Create users
        self.alice = User.objects.create_user(username="alice", email="alice@test.com", password="password123")
        self.bob = User.objects.create_user(username="bob", email="bob@test.com", password="password123")
        
        # Verify KYC for Alice
        self.alice.profile.kyc_status = UserProfile.KYCStatus.VERIFIED
        self.alice.profile.save()
        
        # Create accounts
        self.alice_acc = Account.objects.create(owner=self.alice, balance=Decimal("1000.00"), currency="USD")
        self.bob_acc = Account.objects.create(owner=self.bob, balance=Decimal("500.00"), currency="USD")
        
        # Auth client for Alice
        self.client = APIClient()
        response = self.client.post(reverse("auth-login"), {"username": "alice", "password": "password123"})
        self.access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_transfer_success(self) -> None:
        payload = {
            "from_account": str(self.alice_acc.id),
            "to_account": str(self.bob_acc.id),
            "amount": "100.00",
            "currency": "USD",
            "idempotency_key": "txn-001",
            "note": "Payment for dinner"
        }
        response = self.client.post(reverse("transaction-transfer"), payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.alice_acc.refresh_from_db()
        self.bob_acc.refresh_from_db()
        self.assertEqual(self.alice_acc.balance, Decimal("900.00"))
        self.assertEqual(self.bob_acc.balance, Decimal("600.00"))
        self.assertTrue(Transaction.objects.filter(idempotency_key="txn-001", status=Transaction.Status.COMPLETED).exists())

    def test_transfer_insufficient_funds(self) -> None:
        payload = {
            "from_account": str(self.alice_acc.id),
            "to_account": str(self.bob_acc.id),
            "amount": "2000.00",
            "currency": "USD",
            "idempotency_key": "txn-002"
        }
        response = self.client.post(reverse("transaction-transfer"), payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertEqual(response.data["error"], "INSUFFICIENT_FUNDS")
        # Ensure FAILED record exists
        self.assertTrue(Transaction.objects.filter(status=Transaction.Status.FAILED).exists())

    def test_transfer_duplicate_idempotency_key(self) -> None:
        payload = {
            "from_account": str(self.alice_acc.id),
            "to_account": str(self.bob_acc.id),
            "amount": "50.00",
            "currency": "USD",
            "idempotency_key": "static-key"
        }
        # First request
        self.client.post(reverse("transaction-transfer"), payload, format="json")
        # Second request (duplicate)
        response = self.client.post(reverse("transaction-transfer"), payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # Replayed or fetched existing
        self.assertEqual(Transaction.objects.filter(idempotency_key="static-key").count(), 1)

    def test_transfer_frozen_account(self) -> None:
        self.alice_acc.status = Account.Status.FROZEN
        self.alice_acc.save()
        
        payload = {
            "from_account": str(self.alice_acc.id),
            "to_account": str(self.bob_acc.id),
            "amount": "10.00",
            "currency": "USD",
            "idempotency_key": "txn-frozen"
        }
        response = self.client.post(reverse("transaction-transfer"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "ACCOUNT_NOT_ACTIVE")

    def test_transfer_unauthorized_account(self) -> None:
        # Alice tries to send money FROM Bob's account
        payload = {
            "from_account": str(self.bob_acc.id),
            "to_account": str(self.alice_acc.id),
            "amount": "10.00",
            "currency": "USD",
            "idempotency_key": "txn-steal"
        }
        response = self.client.post(reverse("transaction-transfer"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "ACCOUNT_OWNERSHIP_ERROR")

    def test_list_transactions(self) -> None:
        # Create a successful transaction
        Transaction.objects.create(
            from_account=self.alice_acc,
            to_account=self.bob_acc,
            amount=Decimal("10.00"),
            currency="USD",
            status=Transaction.Status.COMPLETED,
            idempotency_key="list-test-1"
        )
        
        response = self.client.get(reverse("transaction-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
