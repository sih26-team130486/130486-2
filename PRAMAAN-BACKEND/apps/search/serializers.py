"""
search/serializers.py — Lightweight response for search results
"""
from rest_framework import serializers
from apps.documents.models import Document


class DocumentSearchResultSerializer(serializers.ModelSerializer):
    uploader_name   = serializers.SerializerMethodField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    has_custody     = serializers.SerializerMethodField()
    has_certificate = serializers.SerializerMethodField()
    has_redaction   = serializers.SerializerMethodField()
    verification_count = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = [
            'id', 'filename', 'case_id', 'file_type', 'file_size',
            'sha256_hash', 'status', 'status_display',
            'description', 'uploader_name', 'uploaded_at',
            'has_custody', 'has_certificate', 'has_redaction',
            'verification_count',
        ]

    def get_uploader_name(self, obj):
        if obj.uploader:
            return obj.uploader.full_name or obj.uploader.username
        return '—'

    def get_has_custody(self, obj):
        return hasattr(obj, 'custody_chain')

    def get_has_certificate(self, obj):
        return obj.certificates.exists()

    def get_has_redaction(self, obj):
        return obj.redaction_jobs.filter(status='COMPLETED').exists()

    def get_verification_count(self, obj):
        return obj.verifications.count()
