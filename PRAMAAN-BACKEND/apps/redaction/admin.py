"""
redaction/admin.py
"""
from django.contrib import admin
from .models import RedactionJob


@admin.register(RedactionJob)
class RedactionJobAdmin(admin.ModelAdmin):
    list_display  = ['document', 'requested_by', 'pii_count', 'pii_types_detected', 'status', 'created_at']
    list_filter   = ['status']
    search_fields = ['document__filename', 'requested_by__username']
    readonly_fields = [
        'id', 'document', 'requested_by', 'pii_types_detected',
        'pii_count', 'redaction_report', 'created_at', 'completed_at',
    ]
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False  # Created only via API
