"""
verification/models.py — Tamper detection result store
"""
import uuid
from django.db import models
from django.conf import settings


class VerificationResult(models.Model):
    """Stores result of each hash verification attempt."""

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document      = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    verified_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications_done'
    )
    original_hash = models.CharField(max_length=64, help_text='Hash stored at upload time')
    computed_hash = models.CharField(max_length=64, help_text='Hash re-computed at verify time')
    is_tampered   = models.BooleanField(default=False)
    verified_at   = models.DateTimeField(auto_now_add=True)
    notes         = models.TextField(blank=True)

    class Meta:
        db_table = 'pramaan_verifications'
        ordering = ['-verified_at']
        verbose_name = 'Verification Result'
        verbose_name_plural = 'Verification Results'

    def __str__(self):
        outcome = '🚨 TAMPERED' if self.is_tampered else '✅ VERIFIED'
        return f'{self.document.filename} — {outcome} @ {self.verified_at}'
