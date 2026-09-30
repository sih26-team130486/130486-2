"""
audit/serializers.py
"""
from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user          = UserSerializer(read_only=True)
    document_name = serializers.SerializerMethodField()
    action_display   = serializers.CharField(source='get_action_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    result_display   = serializers.CharField(source='get_result_display', read_only=True)

    class Meta:
        model  = AuditLog
        fields = [
            'id', 'user', 'action', 'action_display',
            'document_name', 'case_id',
            'result', 'result_display',
            'severity', 'severity_display',
            'ip_address', 'timestamp', 'metadata',
        ]

    def get_document_name(self, obj):
        return obj.document.filename if obj.document else '—'
