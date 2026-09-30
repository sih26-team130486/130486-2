"""
certificates/admin.py
"""
from django.contrib import admin
from .models import EvidenceCertificate


@admin.register(EvidenceCertificate)
class EvidenceCertificateAdmin(admin.ModelAdmin):
    list_display  = ['certificate_number', 'document', 'certificate_type', 'generated_by', 'is_valid', 'generated_at']
    list_filter   = ['certificate_type', 'is_valid']
    search_fields = ['certificate_number', 'document__filename']
    readonly_fields = ['id', 'certificate_number', 'sha256_of_pdf', 'generated_at']
    ordering = ['-generated_at']

    def has_change_permission(self, request, obj=None):
        # Certificates are immutable — only validity flag can be toggled
        return True

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing existing
            return self.readonly_fields + ('certificate_type', 'document', 'generated_by', 'pdf_file')
        return self.readonly_fields
