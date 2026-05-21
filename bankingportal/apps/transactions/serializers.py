from rest_framework import serializers
from apps.transactions.models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    """
    Transaction serializer with UUID masking for security on counterside accounts.
    """
    from_account_display = serializers.SerializerMethodField()
    to_account_display = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'from_account_display', 'to_account_display', 
            'amount', 'currency', 'status', 'timestamp', 'note'
        ]
        read_only_fields = fields

    def get_from_account_display(self, obj):
        user = self.context['request'].user
        if obj.from_account.owner == user:
            return str(obj.from_account_id)
        return "****-****-****-****"

    def get_to_account_display(self, obj):
        user = self.context['request'].user
        if obj.to_account.owner == user:
            return str(obj.to_account_id)
        return "****-****-****-****"

class TransferRequestSerializer(serializers.Serializer):
    """
    Serializer for validating transfer requests.
    Used for API documentation.
    """
    from_account = serializers.UUIDField(required=True)
    to_account = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, required=True)
    currency = serializers.CharField(max_length=3, default='USD')
    note = serializers.CharField(max_length=255, required=False)
