"""
audit/models.py — Immutable audit log for all PRAMAAN actions
"""
import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN',        'Login'),
        ('LOGOUT',       'Logout'),
        ('UPLOAD',       'Document Upload'),
        ('VIEW',         'Document View'),
        ('DOWNLOAD',     'Document Download'),
        ('DELETE',       'Document Delete'),
        ('VERIFY',       'Integrity Verify'),
        ('TAMPER_ALERT', 'Tamper Alert'),
        ('CREATE_USER',       'Create User'),
        ('UPDATE_USER',       'Update User'),
        ('CUSTODY_TRANSFER',  'Custody Transfer'),
        ('CERT_GENERATE',     'Certificate Generate'),
        ('PII_REDACT',        'PII Redaction'),
        ('SEARCH',            'Document Search'),
    ]

    SEVERITY_CHOICES = [
        ('INFO',     'Info'),
        ('WARNING',  'Warning'),
        ('CRITICAL', 'Critical'),
    ]

    RESULT_CHOICES = [
        ('SUCCESS',         'Success'),
        ('FAILED',          'Failed'),
        ('TAMPER_DETECTED', 'Tamper Detected'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    document   = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    case_id    = models.CharField(max_length=100, blank=True)
    result     = models.CharField(max_length=20, choices=RESULT_CHOICES, default='SUCCESS')
    severity   = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='INFO')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata   = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'pramaan_audit_logs'
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        doc_str  = self.document.filename if self.document else '—'
        return f'[{self.severity}] {user_str} → {self.action} on {doc_str} @ {self.timestamp}'
