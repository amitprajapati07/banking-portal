import uuid
from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    """
    Financial account model with optimistic locking support and high-performance indexing.
    Represents a user's balance in a specific currency.
    """
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        FROZEN = "FROZEN", "Frozen"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="accounts", 
        db_index=True
    )
    balance = models.DecimalField(max_digits=19, decimal_places=4, default=0.0000)
    currency = models.CharField(max_length=3, default="USD", db_index=True)
    status = models.CharField(
        max_length=10, 
        choices=Status.choices, 
        default=Status.ACTIVE, 
        db_index=True
    )
    
    # Optimistic locking version
    version = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["owner", "currency"]),
        ]

    def __str__(self):
        return f"{self.owner.username} - {self.currency} ({self.status})"