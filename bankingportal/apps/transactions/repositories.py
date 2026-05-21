"""Repository layer for the transactions domain."""

import logging
from typing import Optional
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models import QuerySet

from apps.transactions.models import Transaction

logger = logging.getLogger(__name__)


class TransactionRepository:
    """Data-access methods for the :class:`~apps.transactions.models.Transaction` model."""

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_id(transaction_id: UUID) -> Optional[Transaction]:
        """Return the :class:`Transaction` with *transaction_id* or ``None``."""
        try:
            return (
                Transaction.objects.select_related(
                    "from_account__owner", "to_account__owner"
                ).get(id=transaction_id)
            )
        except Transaction.DoesNotExist:
            return None

    @staticmethod
    def get_by_idempotency_key(key: str) -> Optional[Transaction]:
        """Return an existing transaction for *key* or ``None``."""
        try:
            return Transaction.objects.get(idempotency_key=key)
        except Transaction.DoesNotExist:
            return None

    @staticmethod
    def list_for_user(user: User) -> QuerySet:
        """
        Return all transactions where *user* owns either the source or
        destination account, ordered by most-recent first.
        """
        return (
            Transaction.objects.filter(
                from_account__owner=user,
            )
            | Transaction.objects.filter(
                to_account__owner=user,
            )
        ).select_related(
            "from_account__owner", "to_account__owner"
        ).order_by("-timestamp").distinct()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create(**kwargs) -> Transaction:
        """Create and persist a new :class:`Transaction`."""
        txn = Transaction.objects.create(**kwargs)
        logger.info(
            "Transaction created: id=%s status=%s amount=%s %s",
            txn.id,
            txn.status,
            txn.amount,
            txn.currency,
        )
        return txn
