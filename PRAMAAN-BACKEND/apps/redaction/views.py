"""
redaction/views.py — PII Detection and Redaction API

POST /api/v1/redaction/detect/        Scan only — no file change, returns PII report
POST /api/v1/redaction/redact/        Detect + create redacted copy, store job
GET  /api/v1/redaction/               List all redaction jobs (IO/ADMIN)
GET  /api/v1/redaction/<id>/          Redaction job detail + full PII report
GET  /api/v1/redaction/<id>/download/ Download the redacted file copy
"""
import os
from django.utils import timezone
from django.core.files.base import ContentFile
from django.http import FileResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrIO, IsAnyRole
from apps.audit.utils import log_action
from apps.documents.models import Document
from .models import RedactionJob
from .serializers import (
    RedactionJobSerializer, RedactionJobListSerializer,
    DetectPIISerializer, RedactDocumentSerializer,
)
from .pii_engine import process_file, scan_text


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _get_document(doc_id):
    try:
        return Document.objects.get(pk=doc_id)
    except Document.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Detect Only (no file modification)
# ---------------------------------------------------------------------------
class DetectPIIView(APIView):
    """
    POST /api/v1/redaction/detect/
    Scans the document for PII and returns a report.
    The original file is NOT modified. No DB record created.
    Roles: ADMIN, IO
    """
    permission_classes = [IsAdminOrIO]

    def post(self, request):
        serializer = DetectPIISerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        doc = _get_document(serializer.validated_data['document_id'])
        if not doc:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not doc.file or not os.path.exists(doc.file.path):
            return Response({'error': 'Document file not found on storage.'}, status=status.HTTP_404_NOT_FOUND)

        # Run PII engine — scan only
        try:
            report, _, _ = process_file(doc.file.path)
        except Exception as e:
            return Response({'error': f'PII scan failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        log_action(
            user=request.user,
            action='PII_REDACT',
            document=doc,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={
                'action_type':     'DETECT_ONLY',
                'pii_count':       report.total_found,
                'pii_types':       report.types_found,
                'document_name':   doc.filename,
            }
        )

        return Response({
            'document':    str(doc.id),
            'filename':    doc.filename,
            'scan_result': {
                'total_pii_found':  report.total_found,
                'pii_types_found':  report.types_found,
                'matches':          report.matches,
                'is_clean':         report.total_found == 0,
            },
            'note': 'Detection only — original file unchanged. Use /redact/ to create a redacted copy.',
        })


# ---------------------------------------------------------------------------
# Detect + Redact (creates a new redacted copy)
# ---------------------------------------------------------------------------
class RedactDocumentView(APIView):
    """
    POST /api/v1/redaction/redact/
    Scans for PII and stores a redacted copy. Original is untouched.
    Roles: ADMIN, IO
    """
    permission_classes = [IsAdminOrIO]

    def post(self, request):
        serializer = RedactDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        doc = _get_document(serializer.validated_data['document_id'])
        if not doc:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not doc.file or not os.path.exists(doc.file.path):
            return Response({'error': 'Document file not found on storage.'}, status=status.HTTP_404_NOT_FOUND)

        # Create a pending job record
        job = RedactionJob.objects.create(
            document     = doc,
            requested_by = request.user,
            status       = 'PENDING',
        )

        try:
            report, redacted_bytes, mime = process_file(doc.file.path)

            # Determine output filename
            import os as _os
            base, ext = _os.path.splitext(doc.filename)
            out_filename = f'{base}_REDACTED{ext}'

            # Save redacted file
            job.redacted_file.save(out_filename, ContentFile(redacted_bytes), save=False)
            job.pii_types_detected = report.types_found
            job.pii_count          = report.total_found
            job.redaction_report   = report.matches
            job.status             = 'COMPLETED'
            job.completed_at       = timezone.now()
            job.save()

        except Exception as e:
            job.status        = 'FAILED'
            job.error_message = str(e)
            job.save(update_fields=['status', 'error_message'])
            return Response(
                {'error': f'Redaction failed: {str(e)}', 'job_id': str(job.id)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        severity = 'WARNING' if report.total_found > 0 else 'INFO'
        log_action(
            user=request.user,
            action='PII_REDACT',
            document=doc,
            result='SUCCESS',
            severity=severity,
            ip_address=get_client_ip(request),
            metadata={
                'action_type':   'REDACTED',
                'job_id':        str(job.id),
                'pii_count':     report.total_found,
                'pii_types':     report.types_found,
                'output_file':   out_filename,
            }
        )

        return Response({
            'message':     f'Redaction complete. {report.total_found} PII entities redacted.',
            'job':         RedactionJobSerializer(job).data,
        }, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------
class RedactionJobListView(APIView):
    """GET /api/v1/redaction/  — List all jobs. Roles: ADMIN, IO"""
    permission_classes = [IsAdminOrIO]

    def get(self, request):
        qs = RedactionJob.objects.select_related('document', 'requested_by').all()
        doc_id = request.query_params.get('document_id')
        status_filter = request.query_params.get('status')
        if doc_id:
            qs = qs.filter(document__id=doc_id)
        if status_filter:
            qs = qs.filter(status__iexact=status_filter)
        return Response({
            'count': qs.count(),
            'results': RedactionJobListSerializer(qs, many=True).data,
        })


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------
class RedactionJobDetailView(APIView):
    """GET /api/v1/redaction/<id>/"""
    permission_classes = [IsAnyRole]

    def get(self, request, pk):
        try:
            job = RedactionJob.objects.select_related('document', 'requested_by').get(pk=pk)
        except RedactionJob.DoesNotExist:
            return Response({'error': 'Redaction job not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RedactionJobSerializer(job).data)


# ---------------------------------------------------------------------------
# Download Redacted File
# ---------------------------------------------------------------------------
class DownloadRedactedFileView(APIView):
    """
    GET /api/v1/redaction/<id>/download/
    Stream the redacted file. Roles: ADMIN, IO, COURT
    """
    permission_classes = [IsAnyRole]

    def get(self, request, pk):
        try:
            job = RedactionJob.objects.select_related('document').get(pk=pk)
        except RedactionJob.DoesNotExist:
            return Response({'error': 'Redaction job not found.'}, status=status.HTTP_404_NOT_FOUND)

        if job.status != 'COMPLETED':
            return Response(
                {'error': f'Redaction job is {job.get_status_display()}, not completed yet.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not job.redacted_file or not os.path.exists(job.redacted_file.path):
            return Response({'error': 'Redacted file not found on storage.'}, status=status.HTTP_404_NOT_FOUND)

        log_action(
            user=request.user,
            action='DOWNLOAD',
            document=job.document,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={'type': 'REDACTED_FILE_DOWNLOAD', 'job_id': str(job.id)}
        )

        import os as _os
        _, ext = _os.path.splitext(job.redacted_file.name)
        content_type = 'application/pdf' if ext.lower() == '.pdf' else 'text/plain'

        response = FileResponse(
            open(job.redacted_file.path, 'rb'),
            content_type=content_type
        )
        filename = _os.path.basename(job.redacted_file.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-PII-Count']         = str(job.pii_count)
        response['X-PII-Types']         = ','.join(job.pii_types_detected)
        return response
