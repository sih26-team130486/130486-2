"""
documents/admin.py
"""
from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ['filename', 'case_id', 'status', 'sha256_hash', 'uploader', 'uploaded_at']
    list_filter   = ['status', 'file_type']
    search_fields = ['filename', 'case_id', 'sha256_hash']
    readonly_fields = ['id', 'sha256_hash', 'file_size', 'uploaded_at', 'updated_at']
    ordering      = ['-uploaded_at']
