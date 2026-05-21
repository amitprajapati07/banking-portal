"""URL patterns for the transactions app."""

from django.urls import path

from apps.transactions.views import (
    TransactionDetailView,
    TransactionListView,
    TransferView,
)

urlpatterns = [
    path("transfer/", TransferView.as_view(), name="transaction-transfer"),
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("<uuid:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
]
