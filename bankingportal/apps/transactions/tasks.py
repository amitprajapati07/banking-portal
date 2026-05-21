import logging
from celery import shared_task
from apps.transactions.models import Transaction

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_transfer_async(self, transaction_id):
    """
    Offloads complex post-transfer logic (external syncing, etc).
    """
    try:
        txn = Transaction.objects.get(id=transaction_id)
        logger.info(f"Background processing for transaction {txn.id}")
    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
    except Exception as exc:
        logger.error(f"Error processing transaction {transaction_id}: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task
def send_transfer_notification(transaction_id):
    """
    Notification service placeholder.
    """
    try:
        txn = Transaction.objects.select_related('from_account__owner', 'to_account__owner').get(id=transaction_id)
        logger.info(f"Notification sent for transaction {txn.id}")
    except Transaction.DoesNotExist:
        pass

@shared_task
def run_fraud_check(transaction_id):
    """
    Fraud detection simulation. Blocks suspicious flows.
    """
    try:
        txn = Transaction.objects.get(id=transaction_id)
        if txn.amount > 10000:
            txn.status = Transaction.Status.FLAGGED
            txn.save(update_fields=['status', 'updated_at'])
            logger.warning(f"Transaction {txn.id} flagged for fraud review")
    except Transaction.DoesNotExist:
        pass
