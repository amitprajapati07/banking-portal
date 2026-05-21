"""Repository layer for the accounts domain.

Encapsulates all ORM queries so service/view layers remain free of raw
queryset logic and the persistence layer is easily replaceable.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models import QuerySet

from apps.accounts.models import Account

logger = logging.getLogger(__name__)


class AccountRepository:
    """Data-access methods for the :class:`~apps.accounts.models.Account` model."""

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_id(account_id: UUID) -> Optional[Account]:
        """Return the :class:`Account` with *account_id* or ``None``."""
        try:
            return (
                Account.objects.select_related("owner")
                .get(id=account_id)
            )
        except Account.DoesNotExist:
            return None

    @staticmethod
    def list_for_user(user: User) -> QuerySet:
        """Return all accounts belonging to *user*, ordered by ``-created_at``."""
        return (
            Account.objects.filter(owner=user)
            .select_related("owner")
            .order_by("-created_at")
        )

    @staticmethod
    def get_for_update(account_ids: list[UUID]) -> QuerySet:
        """
        Return a queryset of accounts locked with ``SELECT FOR UPDATE``.

        Always ordered by primary key to prevent deadlocks.
        """
        ids = [str(aid) for aid in account_ids]
        return (
            Account.objects.select_for_update(nowait=False)
            .filter(id__in=ids)
            .order_by("id")
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        owner: User,
        currency: str,
        initial_balance: Decimal,
    ) -> Account:
        """Create and persist a new :class:`Account`."""
        account = Account.objects.create(
            owner=owner,
            currency=currency.upper(),
            balance=initial_balance,
            status=Account.Status.ACTIVE,
        )
        logger.info(
            "Account created: id=%s owner=%s currency=%s",
            account.id,
            owner.username,
            currency,
        )
        return account

    @staticmethod
    def save(account: Account, update_fields: list[str] | None = None) -> None:
        """Persist changes to *account*."""
        if update_fields:
            account.save(update_fields=update_fields)
        else:
            account.save()
