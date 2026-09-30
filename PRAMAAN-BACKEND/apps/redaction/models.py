"""
redaction/models.py — Tracks each PII redaction job
Original document is NEVER modified. A redacted copy is stored separately.
"""
import uuid
from django.db import models
from django.conf import settings


def redacted_file_path(instance, filename):
    return f'redacted/{instance.id}_{filename}'


class RedactionJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING',   'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED',    'Failed'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document            = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='redaction_jobs'
    )
    requested_by        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='redaction_jobs'
    )
    # Summary of what was found
    pii_types_detected  = models.JSONField(default=list, blank=True)  # e.g. ["AADHAAR","PAN"]
    pii_count           = models.IntegerField(default=0)

    # The redacted copy (original is untouched)
    redacted_file       = models.FileField(
        upload_to=redacted_file_path, null=True, blank=True
    )
    # Full detection report with positions and masked previews
    redaction_report    = models.JSONField(default=list, blank=True)

    status              = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message       = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    completed_at        = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table     = 'pramaan_redaction_jobs'
        ordering     = ['-created_at']
        verbose_name = 'Redaction Job'

    def __str__(self):
        return f'Redaction of {self.document.filename} [{self.status}] — {self.pii_count} PII found'
