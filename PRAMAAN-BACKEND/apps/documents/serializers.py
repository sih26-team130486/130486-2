"""
documents/serializers.py
"""
from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Full document serializer for list and detail views."""
    uploader      = UserSerializer(read_only=True)
    file_size_display = serializers.ReadOnlyField()

    class Meta:
        model  = Document
        fields = [
            'id', 'case_id', 'filename', 'file_type', 'file_size',
            'file_size_display', 'sha256_hash', 'status', 'description',
            'uploader', 'uploaded_at', 'updated_at',
        ]
        read_only_fields = ['id', 'sha256_hash', 'file_size', 'uploaded_at', 'updated_at']


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for the upload endpoint — accepts the file."""
    file = serializers.FileField()

    class Meta:
        model  = Document
        fields = ['case_id', 'file', 'description']

    def validate_file(self, value):
        allowed_types = [
            'application/pdf',
            'image/jpeg', 'image/png',
            'text/plain', 'text/csv',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/zip',
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f'File type "{value.content_type}" is not allowed. '
                'Allowed: PDF, JPEG, PNG, TXT, CSV, DOC, DOCX, ZIP'
            )
        max_size = 50 * 1024 * 1024  # 50 MB
        if value.size > max_size:
            raise serializers.ValidationError('File size must not exceed 50 MB.')
        return value


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    uploader_name = serializers.SerializerMethodField()
    file_size_display = serializers.ReadOnlyField()

    class Meta:
        model  = Document
        fields = [
            'id', 'case_id', 'filename', 'file_type', 'file_size_display',
            'sha256_hash', 'status', 'uploader_name', 'uploaded_at',
        ]

    def get_uploader_name(self, obj):
        return obj.uploader.full_name or obj.uploader.username if obj.uploader else '—'
