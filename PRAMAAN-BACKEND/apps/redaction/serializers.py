"""
redaction/serializers.py
"""
from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.documents.serializers import DocumentListSerializer
from .models import RedactionJob


class RedactionJobSerializer(serializers.ModelSerializer):
    requested_by    = UserSerializer(read_only=True)
    document        = DocumentListSerializer(read_only=True)
    status_display  = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = RedactionJob
        fields = [
            'id', 'document', 'requested_by',
            'pii_types_detected', 'pii_count',
            'redaction_report', 'status', 'status_display',
            'error_message', 'created_at', 'completed_at',
        ]


class RedactionJobListSerializer(serializers.ModelSerializer):
    document_name  = serializers.SerializerMethodField()
    requested_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = RedactionJob
        fields = [
            'id', 'document_name', 'requested_by_name',
            'pii_types_detected', 'pii_count',
            'status', 'status_display', 'created_at',
        ]

    def get_document_name(self, obj):
        return obj.document.filename if obj.document else '—'

    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return obj.requested_by.full_name or obj.requested_by.username
        return '—'


class DetectPIISerializer(serializers.Serializer):
    """Input for POST /redaction/detect/"""
    document_id = serializers.UUIDField()


class RedactDocumentSerializer(serializers.Serializer):
    """Input for POST /redaction/redact/"""
    document_id = serializers.UUIDField()
