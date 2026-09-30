"""
custody/models.py — Chain of Custody models
CustodyChain: tracks who currently holds a piece of evidence
CustodyTransfer: immutable log of every handover event
"""
import uuid
from django.db import models
from django.conf import settings


class CustodyChain(models.Model):
    """
    One record per document — represents the current state of custody.
    Updated each time a transfer is confirmed.
    """
    STATUS_CHOICES = [
        ('REGISTERED',   'Registered'),
        ('IN_TRANSFER',  'In Transfer'),
        ('WITH_CFSL',    'With CFSL Lab'),
        ('WITH_COURT',   'With Court'),
        ('RETURNED',     'Returned to IO'),
        ('ARCHIVED',     'Archived'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document         = models.OneToOneField(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='custody_chain'
    )
    current_holder   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='custody_holdings'
    )
    current_location = models.CharField(max_length=255, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'pramaan_custody_chains'
        ordering     = ['-created_at']
        verbose_name = 'Custody Chain'

    def __str__(self):
        holder = self.current_holder.full_name if self.current_holder else 'Unknown'
        return f'{self.document.filename} -> {holder} [{self.status}]'


class CustodyTransfer(models.Model):
    """
    One record per transfer event — immutable once confirmed.
    Captures a SHA-256 hash snapshot at transfer time to prove integrity.
    """
    STATUS_CHOICES = [
        ('PENDING',   'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED',  'Rejected'),
    ]

    id                        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    custody_chain             = models.ForeignKey(
        CustodyChain,
        on_delete=models.CASCADE,
        related_name='transfers'
    )
    from_user                 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfers_sent'
    )
    to_user                   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfers_received'
    )
    from_location             = models.CharField(max_length=255, blank=True)
    to_location               = models.CharField(max_length=255, blank=True)
    transfer_reason           = models.TextField(blank=True)
    status                    = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    initiated_at              = models.DateTimeField(auto_now_add=True)
    confirmed_at              = models.DateTimeField(null=True, blank=True)
    notes                     = models.TextField(blank=True)
    # Hash snapshot at time of transfer — forensic proof of state
    document_hash_at_transfer = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table     = 'pramaan_custody_transfers'
        ordering     = ['-initiated_at']
        verbose_name = 'Custody Transfer'

    def __str__(self):
        frm  = self.from_user.full_name if self.from_user else '?'
        to   = self.to_user.full_name if self.to_user else '?'
        return f'Transfer: {frm} -> {to} [{self.status}]'
