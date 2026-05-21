from rest_framework import generics
from rest_framework.response import Response
from apps.accounts.models import Account
from apps.accounts.serializers import AccountListSerializer, AccountDetailSerializer, AccountCreateSerializer
from core.pagination import AccountPagePagination

class AccountListCreateView(generics.ListCreateAPIView):
    """
    Optimized account listing and creation.
    Uses .only() to fetch required fields and select_related for ownership check.
    """
    pagination_class = AccountPagePagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AccountCreateSerializer
        return AccountListSerializer

    def get_queryset(self):
        return Account.objects.select_related('owner__profile').filter(
            owner=self.request.user
        ).only('id', 'currency', 'status')

class AccountDetailView(generics.RetrieveAPIView):
    """
    Detailed account view.
    """
    serializer_class = AccountDetailSerializer

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)

class AccountStatusView(generics.RetrieveAPIView):
    """
    Returns only the status of the account.
    """
    serializer_class = AccountDetailSerializer # We can use a simpler one if needed

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({"id": instance.id, "status": instance.status})
