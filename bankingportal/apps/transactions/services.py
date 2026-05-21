import logging
import uuid as uuid_lib
from decimal import Decimal
from django.db import transaction as db_transaction
from django.db import models
from apps.accounts.models import Account
from apps.accounts.services import AccountService
from apps.transactions.models import Transaction
from core.exceptions import (
    InsufficientFundsError, AccountNotActiveError, 
    AccountOwnershipError, ConcurrentUpdateError
)

logger = logging.getLogger(__name__)

class TransferService:
    """
    High-performance transfer processor.
    Uses deterministic locking to prevent deadlocks and optimistic locking for balance updates.
    """
    
    @staticmethod
    def execute(from_account_id, to_account_id, amount, currency, idempotency_key, user):
        from apps.transactions.tasks import send_transfer_notification, run_fraud_check
        
        # 1. Deterministic locking order to prevent deadlocks
        account_ids = sorted([str(from_account_id), str(to_account_id)])
        
        with db_transaction.atomic():
            # Lock the records with pessimistic locking
            accounts_qs = Account.objects.select_for_update().filter(id__in=account_ids).order_by('id')
            account_map = {str(acc.id): acc for acc in accounts_qs}
            
            if len(account_map) != 2:
                raise ValueError("Invalid account identifiers")
                
            from_account = account_map[str(from_account_id)]
            to_account = account_map[str(to_account_id)]
            
            # 2. Domain Validations
            if from_account.owner != user:
                raise AccountOwnershipError()
                
            if from_account.status != Account.Status.ACTIVE or to_account.status != Account.Status.ACTIVE:
                raise AccountNotActiveError()
                
            if from_account.balance < amount:
                raise InsufficientFundsError()
            
            if from_account.currency != currency or to_account.currency != currency:
                raise ValueError("Currency mismatch")

            # 3. Optimistic Balance Updates
            from_account_version = from_account.version
            to_account_version = to_account.version
            
            # Atomic subtraction with optimistic version check
            updated_from = Account.objects.filter(id=from_account.id, version=from_account_version).update(
                balance=models.F('balance') - amount,
                version=from_account_version + 1
            )
            
            # Atomic addition with optimistic version check
            updated_to = Account.objects.filter(id=to_account.id, version=to_account_version).update(
                balance=models.F('balance') + amount,
                version=to_account_version + 1
            )
            
            if updated_from == 0 or updated_to == 0:
                raise ConcurrentUpdateError()
                
            # 4. Record Transaction
            txn = Transaction.objects.create(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key,
                status=Transaction.Status.COMPLETED
            )
            
            # 5. Invalidate Caches
            AccountService.invalidate_account_cache(from_account.id)
            AccountService.invalidate_account_cache(to_account.id)
            
            # 6. Trigger Async background tasks after DB commit
            db_transaction.on_commit(lambda: send_transfer_notification.delay(txn.id))
            db_transaction.on_commit(lambda: run_fraud_check.delay(txn.id))
            
            return txn
