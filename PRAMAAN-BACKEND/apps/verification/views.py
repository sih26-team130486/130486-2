"""
verification/views.py — Tamper detection engine

Core flow:
  1. Load document by ID
  2. Re-compute SHA-256 of the stored file
  3. Compare with original hash stored at upload
  4. If mismatch → mark document TAMPERED + create alert + audit log CRITICAL
  5. If match → mark document VERIFIED + audit log INFO
"""
import os
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrIO, IsAnyRole
from apps.audit.utils import log_action
from apps.documents.models import Document
from apps.documents.utils import compute_sha256_from_path
from .models import VerificationResult
from .serializers import VerificationResultSerializer


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


class VerifyDocumentView(APIView):
    """
    POST /api/v1/verification/<doc_id>/verify/

    Re-hashes the stored file and compares against original hash.
    Returns verdict: VERIFIED or TAMPERED.
    Roles: ADMIN, IO
    """
    permission_classes = [IsAdminOrIO]

    def post(self, request, doc_id):
        # 1. Get document
        try:
            doc = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 2. Check file exists on disk
        if not doc.file or not os.path.exists(doc.file.path):
            return Response({'error': 'File not found on storage. Cannot verify.'}, status=status.HTTP_404_NOT_FOUND)

        # 3. Re-compute SHA-256 from stored file
        computed_hash = compute_sha256_from_path(doc.file.path)
        original_hash = doc.sha256_hash

        # 4. Compare hashes
        is_tampered = (computed_hash != original_hash)

        # 5. Update document status
        doc.status = 'TAMPERED' if is_tampered else 'VERIFIED'
        doc.save(update_fields=['status', 'updated_at'])

        # 6. Store verification result
        result = VerificationResult.objects.create(
            document      = doc,
            verified_by   = request.user,
            original_hash = original_hash,
            computed_hash = computed_hash,
            is_tampered   = is_tampered,
            notes         = request.data.get('notes', ''),
        )

        # 7. Audit log — CRITICAL if tampered, INFO if clean
        if is_tampered:
            log_action(
                user=request.user,
                action='TAMPER_ALERT',
                document=doc,
                result='TAMPER_DETECTED',
                severity='CRITICAL',
                ip_address=get_client_ip(request),
                metadata={
                    'filename': doc.filename,
                    'original_hash': original_hash,
                    'computed_hash': computed_hash,
                    'verification_id': str(result.id),
                }
            )
        else:
            log_action(
                user=request.user,
                action='VERIFY',
                document=doc,
                result='SUCCESS',
                severity='INFO',
                ip_address=get_client_ip(request),
                metadata={
                    'filename': doc.filename,
                    'hash': original_hash,
                }
            )

        serializer = VerificationResultSerializer(result)
        response_status = status.HTTP_200_OK

        return Response({
            'verification': serializer.data,
            'verdict': 'TAMPERED' if is_tampered else 'VERIFIED',
            'message': (
                f'[CRITICAL] TAMPER DETECTED! Hash mismatch on "{doc.filename}". '
                f'File may have been altered after upload.'
            ) if is_tampered else (
                f'[OK] Document "{doc.filename}" integrity verified. Hash matches original.'
            ),
        }, status=response_status)


class VerificationListView(APIView):
    """
    GET /api/v1/verification/
    List all verification results with optional doc_id filter.
    Roles: ADMIN, IO, COURT
    """
    permission_classes = [IsAnyRole]

    def get(self, request):
        qs = VerificationResult.objects.select_related('document', 'verified_by').all()

        # Filter by document
        doc_id = request.query_params.get('document_id')
        tampered = request.query_params.get('tampered')

        if doc_id:
            qs = qs.filter(document__id=doc_id)
        if tampered is not None:
            qs = qs.filter(is_tampered=(tampered.lower() == 'true'))

        serializer = VerificationResultSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'results': serializer.data,
        })


class VerificationDetailView(APIView):
    """
    GET /api/v1/verification/<id>/
    Roles: ADMIN, IO, COURT
    """
    permission_classes = [IsAnyRole]

    def get(self, request, pk):
        try:
            result = VerificationResult.objects.select_related('document', 'verified_by').get(pk=pk)
        except VerificationResult.DoesNotExist:
            return Response({'error': 'Verification record not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(VerificationResultSerializer(result).data)
