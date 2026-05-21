import uuid
from django.db import models
from apps.accounts.models import Account

class Transaction(models.Model):
    """
    Immutable transaction record with composite indexing for high-performance querying
    of debit/credit histories and duplicate detection.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        FLAGGED = "FLAGGED", "Flagged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_account = models.ForeignKey(
        Account, 
        related_name="debits", 
        on_delete=models.PROTECT
    )
    to_account = models.ForeignKey(
        Account, 
        related_name="credits", 
        on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=10, 
        choices=Status.choices, 
        default=Status.PENDING,
        db_index=True
    )
    idempotency_key = models.CharField(max_length=255, unique=True)
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["from_account", "status"]),
            models.Index(fields=["to_account", "status"]),
            models.Index(fields=["from_account", "timestamp"]),
            models.Index(fields=["idempotency_key"]),
        ]

    def __str__(self):
        return f"{self.from_account_id} -> {self.to_account_id}: {self.amount} {self.currency}"