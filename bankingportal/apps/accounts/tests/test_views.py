"""Integration tests for account API endpoints."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import Account


def _create_user(username: str = "alice", password: str = "SecurePass123!") -> User:
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )


def _auth_client(username: str, password: str) -> APIClient:
    client = APIClient()
    response = client.post(
        reverse("auth-login"),
        {"username": username, "password": password},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


def _create_account(
    owner: User,
    currency: str = "USD",
    balance: Decimal = Decimal("1000.0000"),
    status_val: str = Account.Status.ACTIVE,
) -> Account:
    return Account.objects.create(
        owner=owner,
        currency=currency,
        balance=balance,
        status=status_val,
    )


class AccountCreateTest(APITestCase):
    """POST /api/v1/accounts/."""

    def setUp(self) -> None:
        self.user = _create_user()
        self.client = _auth_client("alice", "SecurePass123!")

    def test_create_account_success(self) -> None:
        response = self.client.post(
            reverse("account-list-create"),
            {"currency": "USD", "initial_balance": "500.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["currency"], "USD")
        self.assertTrue(Account.objects.filter(owner=self.user).exists())

    def test_create_account_invalid_currency(self) -> None:
        response = self.client.post(
            reverse("account-list-create"),
            {"currency": "US"},  # too short
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_account_unauthenticated(self) -> None:
        self.client.credentials()
        response = self.client.post(
            reverse("account-list-create"),
            {"currency": "USD"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AccountListTest(APITestCase):
    """GET /api/v1/accounts/ — users see only their own accounts."""

    def setUp(self) -> None:
        self.alice = _create_user("alice")
        self.bob = _create_user("bob")
        _create_account(self.alice)
        _create_account(self.bob)
        self.client = _auth_client("alice", "SecurePass123!")

    def test_list_accounts_only_own(self) -> None:
        response = self.client.get(reverse("account-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [a["id"] for a in response.data["results"]]
        for acc_id in ids:
            self.assertEqual(
                Account.objects.get(id=acc_id).owner, self.alice
            )

    def test_list_does_not_expose_balance(self) -> None:
        response = self.client.get(reverse("account-list-create"))
        for acc in response.data["results"]:
            self.assertNotIn("balance", acc)


class AccountDetailTest(APITestCase):
    """GET /api/v1/accounts/{id}/ — exposes balance to owner only."""

    def setUp(self) -> None:
        self.alice = _create_user("alice")
        self.bob = _create_user("bob")
        self.alice_acc = _create_account(self.alice, balance=Decimal("250.0000"))
        self.client = _auth_client("alice", "SecurePass123!")

    def test_detail_exposes_balance(self) -> None:
        response = self.client.get(
            reverse("account-detail", kwargs={"pk": str(self.alice_acc.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("balance", response.data)

    def test_detail_forbidden_for_non_owner(self) -> None:
        bob_client = _auth_client("bob", "SecurePass123!")
        response = bob_client.get(
            reverse("account-detail", kwargs={"pk": str(self.alice_acc.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AccountStatusTest(APITestCase):
    """PATCH /api/v1/accounts/{id}/status/."""

    def setUp(self) -> None:
        self.alice = _create_user("alice")
        self.bob = _create_user("bob")
        self.acc = _create_account(self.alice)
        self.client = _auth_client("alice", "SecurePass123!")

    def test_freeze_account(self) -> None:
        response = self.client.patch(
            reverse("account-status", kwargs={"pk": str(self.acc.id)}),
            {"status": "FROZEN"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.acc.refresh_from_db()
        self.assertEqual(self.acc.status, Account.Status.FROZEN)

    def test_freeze_account_non_owner_forbidden(self) -> None:
        bob_client = _auth_client("bob", "SecurePass123!")
        response = bob_client.patch(
            reverse("account-status", kwargs={"pk": str(self.acc.id)}),
            {"status": "FROZEN"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
