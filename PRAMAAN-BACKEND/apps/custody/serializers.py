"""
custody/serializers.py
"""
from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.documents.serializers import DocumentListSerializer
from .models import CustodyChain, CustodyTransfer


class CustodyTransferSerializer(serializers.ModelSerializer):
    from_user    = UserSerializer(read_only=True)
    to_user      = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = CustodyTransfer
        fields = [
            'id', 'from_user', 'to_user',
            'from_location', 'to_location',
            'transfer_reason', 'status', 'status_display',
            'initiated_at', 'confirmed_at', 'notes',
            'document_hash_at_transfer',
        ]


class CustodyChainSerializer(serializers.ModelSerializer):
    document       = DocumentListSerializer(read_only=True)
    current_holder = UserSerializer(read_only=True)
    transfers      = CustodyTransferSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transfer_count = serializers.SerializerMethodField()

    class Meta:
        model  = CustodyChain
        fields = [
            'id', 'document', 'current_holder', 'current_location',
            'status', 'status_display', 'transfer_count',
            'created_at', 'updated_at', 'transfers',
        ]

    def get_transfer_count(self, obj):
        return obj.transfers.count()


class CustodyChainListSerializer(serializers.ModelSerializer):
    """Lightweight — no nested transfers for list views."""
    document_name    = serializers.SerializerMethodField()
    current_holder_name = serializers.SerializerMethodField()
    status_display   = serializers.CharField(source='get_status_display', read_only=True)
    transfer_count   = serializers.SerializerMethodField()

    class Meta:
        model  = CustodyChain
        fields = [
            'id', 'document_name', 'current_holder_name',
            'current_location', 'status', 'status_display',
            'transfer_count', 'created_at', 'updated_at',
        ]

    def get_document_name(self, obj):
        return obj.document.filename if obj.document else '—'

    def get_current_holder_name(self, obj):
        if obj.current_holder:
            return obj.current_holder.full_name or obj.current_holder.username
        return '—'

    def get_transfer_count(self, obj):
        return obj.transfers.count()


class InitiateTransferSerializer(serializers.Serializer):
    """Input for POST /custody/<id>/transfer/"""
    to_user_id      = serializers.UUIDField()
    to_location     = serializers.CharField(max_length=255)
    transfer_reason = serializers.CharField(max_length=1000, required=False, default='')
    notes           = serializers.CharField(max_length=1000, required=False, default='')
