"""
verification/admin.py
"""
from django.contrib import admin
from .models import VerificationResult


@admin.register(VerificationResult)
class VerificationResultAdmin(admin.ModelAdmin):
    list_display  = ['document', 'verified_by', 'is_tampered', 'verified_at']
    list_filter   = ['is_tampered']
    search_fields = ['document__filename', 'original_hash', 'computed_hash']
    readonly_fields = ['id', 'original_hash', 'computed_hash', 'verified_at']
    ordering = ['-verified_at']
