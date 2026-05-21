from rest_framework import serializers
from apps.accounts.models import Account

class AccountDetailSerializer(serializers.ModelSerializer):
    """
    High-security detail serializer.
    """
    class Meta:
        model = Account
        fields = ['id', 'balance', 'currency', 'status', 'created_at', 'version']
        read_only_fields = fields

class AccountListSerializer(serializers.ModelSerializer):
    """
    Restricted list serializer. Does not expose balance to prevent mass data harvesting.
    """
    class Meta:
        model = Account
        fields = ['id', 'currency', 'status']
        read_only_fields = fields

class AccountCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new accounts.
    """
    class Meta:
        model = Account
        fields = ['currency']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
