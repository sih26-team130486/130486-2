"""
audit/admin.py
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['action', 'user', 'document', 'result', 'severity', 'ip_address', 'timestamp']
    list_filter   = ['action', 'severity', 'result']
    search_fields = ['user__username', 'document__filename', 'case_id', 'ip_address']
    readonly_fields = ['id', 'user', 'action', 'document', 'case_id', 'result', 'severity', 'ip_address', 'timestamp', 'metadata']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False  # Audit logs are immutable — no manual creation

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs are immutable — no editing
