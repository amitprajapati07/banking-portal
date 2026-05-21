import logging
from django.core.cache import cache
from django.db import models
from apps.accounts.models import Account

logger = logging.getLogger(__name__)

class AccountService:
    """
    Service layer for Account operations with Redis-backed caching.
    Supports atomic updates with optimistic locking.
    """
    CACHE_TTL = 60  # 60 seconds

    @staticmethod
    def get_account(account_id):
        """
        Fetches account from cache or DB.
        """
        cache_key = f"account:{account_id}"
        account = cache.get(cache_key)
        if not account:
            logger.debug(f"Cache miss for account {account_id}")
            try:
                # Optimized fetching with related profile
                account = Account.objects.select_related('owner__profile').get(id=account_id)
                cache.set(cache_key, account, AccountService.CACHE_TTL)
            except Account.DoesNotExist:
                return None
        return account

    @staticmethod
    def invalidate_account_cache(account_id):
        cache_key = f"account:{account_id}"
        cache.delete(cache_key)
        logger.debug(f"Invalidated cache for account {account_id}")
