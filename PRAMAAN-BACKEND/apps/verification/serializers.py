"""
verification/serializers.py
"""
from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.documents.serializers import DocumentListSerializer
from .models import VerificationResult


class VerificationResultSerializer(serializers.ModelSerializer):
    verified_by = UserSerializer(read_only=True)
    document    = DocumentListSerializer(read_only=True)
    outcome     = serializers.SerializerMethodField()

    class Meta:
        model  = VerificationResult
        fields = [
            'id', 'document', 'verified_by',
            'original_hash', 'computed_hash',
            'is_tampered', 'outcome',
            'verified_at', 'notes',
        ]

    def get_outcome(self, obj):
        return 'TAMPERED' if obj.is_tampered else 'VERIFIED'
