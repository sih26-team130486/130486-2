"""
audit/utils.py — Helper to create audit log entries from anywhere in the codebase.
"""
from .models import AuditLog


def log_action(
    user=None,
    action='VIEW',
    document=None,
    result='SUCCESS',
    severity='INFO',
    ip_address=None,
    metadata=None,
):
    """
    Create an AuditLog record.
    Call this from any view to record actions without duplicating code.

    Usage:
        log_action(
            user=request.user,
            action='UPLOAD',
            document=doc_instance,
            result='SUCCESS',
            severity='INFO',
            ip_address='1.2.3.4',
            metadata={'filename': 'FIR.pdf', 'sha256': '...'}
        )
    """
    AuditLog.objects.create(
        user       = user,
        action     = action,
        document   = document,
        case_id    = document.case_id if document else '',
        result     = result,
        severity   = severity,
        ip_address = ip_address,
        metadata   = metadata or {},
    )
