"""
certificates/views.py — Certificate generation and download

POST /api/v1/certificates/generate/  — Build PDF, store, return metadata
GET  /api/v1/certificates/           — List all certificates
GET  /api/v1/certificates/<id>/      — Certificate metadata detail
GET  /api/v1/certificates/<id>/download/ — Stream PDF file
"""
import os
import hashlib
from django.core.files.base import ContentFile
from django.http import FileResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrIO, IsAnyRole
from apps.audit.utils import log_action
from apps.documents.models import Document
from apps.verification.models import VerificationResult
from .models import EvidenceCertificate
from .serializers import (
    CertificateSerializer, CertificateListSerializer,
    GenerateCertificateSerializer,
)
from .pdf_generator import generate_certificate_pdf


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


class GenerateCertificateView(APIView):
    """
    POST /api/v1/certificates/generate/
    Generates a ReportLab PDF certificate for a document.
    Roles: ADMIN, IO
    """
    permission_classes = [IsAdminOrIO]

    def post(self, request):
        serializer = GenerateCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vdata    = serializer.validated_data
        doc_id   = vdata['document_id']
        cert_type = vdata['certificate_type']

        # Get the document
        try:
            document = Document.objects.select_related('uploader').get(pk=doc_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get latest verification result (if any)
        verification = (
            VerificationResult.objects
            .filter(document=document)
            .select_related('verified_by')
            .order_by('-verified_at')
            .first()
        )

        # Get custody chain (if any)
        custody_chain = None
        if hasattr(document, 'custody_chain'):
            custody_chain = document.custody_chain
            try:
                custody_chain = (
                    document.custody_chain.__class__.objects
                    .prefetch_related('transfers__from_user', 'transfers__to_user')
                    .select_related('current_holder')
                    .get(pk=document.custody_chain.pk)
                )
            except Exception:
                custody_chain = document.custody_chain

        # Generate certificate number
        cert_number = EvidenceCertificate.generate_cert_number()

        # Generate PDF bytes via ReportLab
        pdf_bytes = generate_certificate_pdf(
            cert_number    = cert_number,
            document       = document,
            generated_by   = request.user,
            verification   = verification,
            custody_chain  = custody_chain,
            cert_type      = cert_type,
        )

        # Compute SHA-256 of the generated PDF
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest().upper()

        # Save PDF to media/certificates/
        pdf_filename = f'{cert_number}.pdf'
        cert = EvidenceCertificate(
            certificate_number  = cert_number,
            document            = document,
            generated_by        = request.user,
            certificate_type    = cert_type,
            sha256_of_pdf       = pdf_hash,
            verification_result = verification,
            is_valid            = True,
        )
        cert.pdf_file.save(pdf_filename, ContentFile(pdf_bytes), save=True)

        # Audit log
        log_action(
            user=request.user,
            action='CERT_GENERATE',
            document=document,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={
                'certificate_number': cert_number,
                'certificate_type':   cert_type,
                'pdf_hash':           pdf_hash,
                'document_filename':  document.filename,
            }
        )

        return Response({
            'message':     f'Certificate {cert_number} generated successfully.',
            'certificate': CertificateSerializer(cert).data,
        }, status=status.HTTP_201_CREATED)


class CertificateListView(APIView):
    """
    GET /api/v1/certificates/
    Roles: ADMIN, IO, COURT
    """
    permission_classes = [IsAnyRole]

    def get(self, request):
        qs = EvidenceCertificate.objects.select_related('document', 'generated_by').all()
        doc_id = request.query_params.get('document_id')
        cert_type = request.query_params.get('type')
        if doc_id:
            qs = qs.filter(document__id=doc_id)
        if cert_type:
            qs = qs.filter(certificate_type__iexact=cert_type)
        return Response({
            'count': qs.count(),
            'results': CertificateListSerializer(qs, many=True).data,
        })


class CertificateDetailView(APIView):
    """GET /api/v1/certificates/<id>/"""
    permission_classes = [IsAnyRole]

    def get(self, request, pk):
        try:
            cert = EvidenceCertificate.objects.select_related(
                'document', 'generated_by', 'verification_result'
            ).get(pk=pk)
        except EvidenceCertificate.DoesNotExist:
            return Response({'error': 'Certificate not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CertificateSerializer(cert).data)


class CertificateDownloadView(APIView):
    """
    GET /api/v1/certificates/<id>/download/
    Stream the PDF certificate for download.
    Roles: ADMIN, IO, COURT
    """
    permission_classes = [IsAnyRole]

    def get(self, request, pk):
        try:
            cert = EvidenceCertificate.objects.select_related('document').get(pk=pk)
        except EvidenceCertificate.DoesNotExist:
            return Response({'error': 'Certificate not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not cert.pdf_file or not os.path.exists(cert.pdf_file.path):
            return Response({'error': 'PDF file not found on storage.'}, status=status.HTTP_404_NOT_FOUND)

        log_action(
            user=request.user,
            action='DOWNLOAD',
            document=cert.document,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={
                'certificate_number': cert.certificate_number,
                'type': 'CERTIFICATE_DOWNLOAD',
            }
        )

        response = FileResponse(
            open(cert.pdf_file.path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{cert.certificate_number}.pdf"'
        )
        response['X-Certificate-Number'] = cert.certificate_number
        response['X-PDF-SHA256']          = cert.sha256_of_pdf
        return response
