"""
certificates/models.py — Evidence Certificate record
Tracks every generated PDF certificate with its own SHA-256 hash.
"""
import uuid
from django.db import models
from django.conf import settings


def certificate_upload_path(instance, filename):
    return f'certificates/{instance.id}_{filename}'


class EvidenceCertificate(models.Model):
    CERT_TYPE_CHOICES = [
        ('INTEGRITY',     'Integrity Certificate'),
        ('CUSTODY_CHAIN', 'Chain of Custody Certificate'),
        ('COURT_EXPORT',  'Court Export Certificate'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate_number  = models.CharField(max_length=50, unique=True, db_index=True)
    document            = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    generated_by        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_certificates'
    )
    certificate_type    = models.CharField(
        max_length=20, choices=CERT_TYPE_CHOICES, default='INTEGRITY'
    )
    pdf_file            = models.FileField(
        upload_to=certificate_upload_path, blank=True, null=True
    )
    # The PDF itself is also hashed — self-verifiable certificate
    sha256_of_pdf       = models.CharField(max_length=64, blank=True)
    verification_result = models.ForeignKey(
        'verification.VerificationResult',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='certificates'
    )
    is_valid            = models.BooleanField(default=True)
    generated_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'pramaan_certificates'
        ordering     = ['-generated_at']
        verbose_name = 'Evidence Certificate'

    def __str__(self):
        return f'{self.certificate_number} — {self.document.filename}'

    @classmethod
    def generate_cert_number(cls):
        """Auto-generate next certificate number: PRMN-CERT-2026-000001"""
        from django.utils import timezone
        year  = timezone.now().year
        count = cls.objects.filter(
            generated_at__year=year
        ).count() + 1
        return f'PRMN-CERT-{year}-{count:06d}'
