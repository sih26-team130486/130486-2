"""
custody/admin.py
"""
from django.contrib import admin
from .models import CustodyChain, CustodyTransfer


@admin.register(CustodyChain)
class CustodyChainAdmin(admin.ModelAdmin):
    list_display  = ['document', 'current_holder', 'current_location', 'status', 'created_at']
    list_filter   = ['status']
    search_fields = ['document__filename', 'current_holder__username', 'current_location']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(CustodyTransfer)
class CustodyTransferAdmin(admin.ModelAdmin):
    list_display  = ['custody_chain', 'from_user', 'to_user', 'status', 'initiated_at', 'confirmed_at']
    list_filter   = ['status']
    search_fields = ['from_user__username', 'to_user__username']
    readonly_fields = ['id', 'initiated_at', 'document_hash_at_transfer']
    ordering = ['-initiated_at']

    def has_change_permission(self, request, obj=None):
        # Transfers are immutable once confirmed
        if obj and obj.status == 'CONFIRMED':
            return False
        return super().has_change_permission(request, obj)
