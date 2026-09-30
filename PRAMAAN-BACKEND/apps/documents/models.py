"""
documents/models.py — Document model with SHA-256 hash storage
"""
import uuid
from django.db import models
from django.conf import settings


def document_upload_path(instance, filename):
    """Store files in media/documents/<case_id>/<filename>."""
    case_folder = instance.case_id.replace('/', '-') if instance.case_id else 'uncategorised'
    return f'documents/{case_folder}/{instance.id}_{filename}'


class Document(models.Model):
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('VERIFIED',   'Verified'),
        ('TAMPERED',   'Tampered'),
        ('ARCHIVED',   'Archived'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_id     = models.CharField(max_length=100, blank=True, db_index=True)
    filename    = models.CharField(max_length=255)
    file        = models.FileField(upload_to=document_upload_path)
    file_type   = models.CharField(max_length=100, blank=True)  # MIME type
    file_size   = models.BigIntegerField(default=0)             # bytes

    # SHA-256 computed at upload — this is the "ground truth" hash
    sha256_hash = models.CharField(max_length=64, db_index=True)

    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    description = models.TextField(blank=True)

    uploader    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pramaan_documents'
        ordering = ['-uploaded_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self):
        return f'{self.filename} [{self.status}]'

    @property
    def file_size_display(self):
        """Human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'
