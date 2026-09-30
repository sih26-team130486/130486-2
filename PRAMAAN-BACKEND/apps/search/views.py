"""
search/views.py — Advanced Document Search

GET /api/v1/search/documents/

Query Parameters:
  q               — Full-text: searches filename, description, case_id
  case_id         — Exact or partial case ID match
  status          — Document status (REGISTERED/VERIFIED/TAMPERED/ARCHIVED)
  file_type       — MIME type filter (e.g. application/pdf)
  uploader        — Matches uploader full_name or username (partial)
  date_from       — Uploaded on or after (YYYY-MM-DD)
  date_to         — Uploaded on or before (YYYY-MM-DD)
  hash            — SHA-256 prefix search (starts-with)
  has_pii         — true/false: only docs with completed redaction jobs
  has_certificate — true/false: only docs with generated certificates
  has_custody     — true/false: only docs registered in custody chain
  sort_by         — Field to sort by (uploaded_at, filename, file_size, status)
                    Prefix with - for descending (e.g. -uploaded_at)
  page            — Page number (default 1)
  page_size       — Results per page (default 20, max 100)
"""
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.permissions import IsAnyRole
from apps.audit.utils import log_action
from apps.documents.models import Document
from .serializers import DocumentSearchResultSerializer


VALID_SORT_FIELDS = {
    'uploaded_at', '-uploaded_at',
    'filename', '-filename',
    'file_size', '-file_size',
    'status', '-status',
    'updated_at', '-updated_at',
}


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def parse_bool(value):
    """Parse 'true'/'false'/'1'/'0' query param to bool or None."""
    if value is None:
        return None
    return value.lower() in ('true', '1', 'yes')


class DocumentSearchView(APIView):
    """
    GET /api/v1/search/documents/
    Advanced document search with 10+ filter parameters.
    Roles: ADMIN, IO, COURT (all authenticated users)
    """
    permission_classes = [IsAnyRole]

    def get(self, request):
        params = request.query_params

        # --- Build base queryset ---
        qs = Document.objects.select_related('uploader').prefetch_related(
            'certificates', 'redaction_jobs', 'verifications'
        )

        # ── 1. Full-text search (filename, description, case_id) ──────────
        q = params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(filename__icontains=q) |
                Q(description__icontains=q) |
                Q(case_id__icontains=q)
            )

        # ── 2. Case ID ────────────────────────────────────────────────────
        case_id = params.get('case_id', '').strip()
        if case_id:
            qs = qs.filter(case_id__icontains=case_id)

        # ── 3. Status ─────────────────────────────────────────────────────
        status_filter = params.get('status', '').strip().upper()
        if status_filter:
            qs = qs.filter(status=status_filter)

        # ── 4. File type (MIME) ───────────────────────────────────────────
        file_type = params.get('file_type', '').strip()
        if file_type:
            qs = qs.filter(file_type__icontains=file_type)

        # ── 5. Uploader name/username ─────────────────────────────────────
        uploader = params.get('uploader', '').strip()
        if uploader:
            qs = qs.filter(
                Q(uploader__full_name__icontains=uploader) |
                Q(uploader__username__icontains=uploader)
            )

        # ── 6. Date range ─────────────────────────────────────────────────
        date_from = params.get('date_from', '').strip()
        date_to   = params.get('date_to', '').strip()
        if date_from:
            qs = qs.filter(uploaded_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(uploaded_at__date__lte=date_to)

        # ── 7. Hash prefix search ─────────────────────────────────────────
        hash_prefix = params.get('hash', '').strip().upper()
        if hash_prefix:
            qs = qs.filter(sha256_hash__startswith=hash_prefix)

        # ── 8. Has PII redaction (completed) ──────────────────────────────
        has_pii = parse_bool(params.get('has_pii'))
        if has_pii is True:
            qs = qs.filter(redaction_jobs__status='COMPLETED').distinct()
        elif has_pii is False:
            qs = qs.exclude(redaction_jobs__status='COMPLETED').distinct()

        # ── 9. Has certificate ────────────────────────────────────────────
        has_cert = parse_bool(params.get('has_certificate'))
        if has_cert is True:
            qs = qs.filter(certificates__isnull=False).distinct()
        elif has_cert is False:
            qs = qs.filter(certificates__isnull=True)

        # ── 10. Has custody chain ─────────────────────────────────────────
        has_custody = parse_bool(params.get('has_custody'))
        if has_custody is True:
            qs = qs.filter(custody_chain__isnull=False)
        elif has_custody is False:
            qs = qs.filter(custody_chain__isnull=True)

        # ── Sorting ───────────────────────────────────────────────────────
        sort_by = params.get('sort_by', '-uploaded_at').strip()
        if sort_by not in VALID_SORT_FIELDS:
            sort_by = '-uploaded_at'
        qs = qs.order_by(sort_by)

        # ── Pagination ────────────────────────────────────────────────────
        try:
            page      = max(1, int(params.get('page', 1)))
            page_size = min(100, max(1, int(params.get('page_size', 20))))
        except (ValueError, TypeError):
            page, page_size = 1, 20

        total_count = qs.count()
        start = (page - 1) * page_size
        end   = start + page_size
        page_qs = qs[start:end]

        serializer = DocumentSearchResultSerializer(page_qs, many=True)

        # Build active_filters for the response (helps frontend show what's active)
        active_filters = {k: v for k, v in params.items()
                          if k not in ('page', 'page_size')}

        # Audit log the search (lightweight — only if a real query is made)
        if any([q, case_id, status_filter, file_type, uploader,
                date_from, date_to, hash_prefix,
                has_pii is not None, has_cert is not None, has_custody is not None]):
            log_action(
                user=request.user,
                action='SEARCH',
                document=None,
                result='SUCCESS',
                severity='INFO',
                ip_address=get_client_ip(request),
                metadata={
                    'query':          q,
                    'filters':        active_filters,
                    'results_found':  total_count,
                }
            )

        return Response({
            'total_count':    total_count,
            'page':           page,
            'page_size':      page_size,
            'total_pages':    (total_count + page_size - 1) // page_size,
            'active_filters': active_filters,
            'results':        serializer.data,
        })
