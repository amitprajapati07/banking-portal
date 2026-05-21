"""
Database-level locking utilities using PostgreSQL SELECT FOR UPDATE.

Locks are always acquired in a consistent primary-key order to prevent
deadlocks when two concurrent transactions attempt to lock the same pair
of accounts in opposite order.
"""

import logging
from typing import Iterable, List
from uuid import UUID

from django.db import models

logger = logging.getLogger(__name__)


def lock_accounts_for_update(
    queryset: models.QuerySet,
    account_ids: Iterable[UUID],
) -> List[models.Model]:
    """
    Lock the given Account rows with SELECT FOR UPDATE (blocking).

    Accounts are always fetched in ascending primary-key order so that any two
    concurrent sessions locking the same pair will always request the locks in
    identical order, eliminating the classic deadlock scenario.

    Args:
        queryset: Base queryset (typically ``Account.objects``).
        account_ids: UUIDs of the accounts to lock.

    Returns:
        List of locked Account instances ordered by ``id``.

    Raises:
        ValueError: If any requested account does not exist.
    """
    ids: List[str] = sorted(str(aid) for aid in account_ids)

    locked: List[models.Model] = list(
        queryset.select_for_update(nowait=False).filter(id__in=ids).order_by("id")
    )

    found_ids = {str(acc.id) for acc in locked}
    missing = set(ids) - found_ids
    if missing:
        raise ValueError(f"Accounts not found: {missing}")

    logger.debug("Acquired row-level locks for accounts: %s", ids)
    return locked
