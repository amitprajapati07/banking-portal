from decimal import Decimal
from rest_framework import generics, filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer, TransferRequestSerializer
from apps.transactions.filters import TransactionFilter
from apps.transactions.services import TransferService
from core.pagination import TransactionCursorPagination
from core.idempotency import idempotency_required
from core.throttles import TransferRateThrottle
from rest_framework.response import Response
from rest_framework import status

class TransactionListView(generics.ListAPIView):
    """
    Highly optimized transaction list view.
    Uses select_related to prevent N+1 queries.
    Uses Cursor Pagination for high-throughput performance.
    """
    serializer_class = TransactionSerializer
    pagination_class = TransactionCursorPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['note', 'idempotency_key']
    ordering_fields = ['timestamp', 'amount']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or user.is_anonymous:
            return Transaction.objects.none()
        
        return Transaction.objects.select_related(
            'from_account__owner', 
            'to_account__owner'
        ).filter(
            Q(from_account__owner=user) | Q(to_account__owner=user)
        )

class TransactionDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a single transaction.
    """
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or user.is_anonymous:
            return Transaction.objects.none()
            
        return Transaction.objects.filter(
            Q(from_account__owner=user) | Q(to_account__owner=user)
        )

class TransferView(generics.CreateAPIView):
    """
    Enterprise transfer endpoint.
    Includes Idempotency protection and rate limiting.
    """
    serializer_class = TransferRequestSerializer
    throttle_classes = [TransferRateThrottle]

    @idempotency_required
    def post(self, request, *args, **kwargs):
        from_id = request.data.get('from_account')
        to_id = request.data.get('to_account')
        amount_raw = request.data.get('amount')
        if not amount_raw:
            return Response({"error": "AMOUNT_REQUIRED"}, status=400)
        
        amount = Decimal(str(amount_raw))
        currency = request.data.get('currency')
        id_key = request.headers.get('Idempotency-Key')

        txn = TransferService.execute(
            from_account_id=from_id,
            to_account_id=to_id,
            amount=amount,
            currency=currency,
            idempotency_key=id_key,
            user=request.user
        )
        
        serializer = TransactionSerializer(txn, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
