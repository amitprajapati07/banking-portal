from django_filters import rest_framework as filters
from django.db.models import Q
from apps.transactions.models import Transaction

class TransactionFilter(filters.FilterSet):
    from_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr='gte')
    to_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr='lte')
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    account_id = filters.UUIDFilter(method='filter_by_account')

    class Meta:
        model = Transaction
        fields = ['status', 'currency']

    def filter_by_account(self, queryset, name, value):
        return queryset.filter(Q(from_account_id=value) | Q(to_account_id=value))
