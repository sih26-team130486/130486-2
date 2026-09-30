"""
certificates/serializers.py
"""
from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.documents.serializers import DocumentListSerializer
from .models import EvidenceCertificate


class CertificateSerializer(serializers.ModelSerializer):
    generated_by         = UserSerializer(read_only=True)
    document             = DocumentListSerializer(read_only=True)
    certificate_type_display = serializers.CharField(
        source='get_certificate_type_display', read_only=True
    )

    class Meta:
        model  = EvidenceCertificate
        fields = [
            'id', 'certificate_number', 'document', 'generated_by',
            'certificate_type', 'certificate_type_display',
            'sha256_of_pdf', 'is_valid', 'generated_at',
        ]


class CertificateListSerializer(serializers.ModelSerializer):
    document_name    = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    certificate_type_display = serializers.CharField(
        source='get_certificate_type_display', read_only=True
    )

    class Meta:
        model  = EvidenceCertificate
        fields = [
            'id', 'certificate_number', 'document_name',
            'generated_by_name', 'certificate_type',
            'certificate_type_display', 'is_valid', 'generated_at',
        ]

    def get_document_name(self, obj):
        return obj.document.filename if obj.document else '—'

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.full_name or obj.generated_by.username
        return '—'


class GenerateCertificateSerializer(serializers.Serializer):
    """Input for POST /certificates/generate/"""
    document_id      = serializers.UUIDField()
    certificate_type = serializers.ChoiceField(
        choices=['INTEGRITY', 'CUSTODY_CHAIN', 'COURT_EXPORT'],
        default='INTEGRITY'
    )
