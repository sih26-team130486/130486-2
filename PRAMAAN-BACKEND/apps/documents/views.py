"""
documents/views.py — Upload, List, Detail, Download, Delete
"""
import os
import mimetypes
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.accounts.permissions import IsAdmin, IsAdminOrIO, IsAnyRole
from apps.audit.utils import log_action
from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer, DocumentListSerializer
from .utils import compute_sha256


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


class DocumentUploadView(APIView):
    """
    POST /api/v1/documents/upload/
    Accepts a multipart file upload, computes SHA-256, stores file + metadata.
    Roles: ADMIN, IO
    """
    permission_classes = [IsAdminOrIO]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']

        # Compute SHA-256 before saving
        sha256 = compute_sha256(uploaded_file)

        # Detect MIME type
        file_type = uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream'

        # Create Document instance
        document = Document(
            case_id     = serializer.validated_data.get('case_id', ''),
            filename    = uploaded_file.name,
            file        = uploaded_file,
            file_type   = file_type,
            file_size   = uploaded_file.size,
            sha256_hash = sha256,
            status      = 'REGISTERED',
            description = serializer.validated_data.get('description', ''),
            uploader    = request.user,
        )
        document.save()

        # Audit log
        log_action(
            user=request.user,
            action='UPLOAD',
            document=document,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={
                'filename': document.filename,
                'sha256': sha256,
                'file_size': document.file_size,
                'case_id': document.case_id,
            }
        )

        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )


class DocumentListView(APIView):
    """
    GET /api/v1/documents/
    List all documents with optional filtering by case_id or status.
    Roles: ADMIN, IO, COURT
    """
    permission_classes = [IsAnyRole]

    def get(self, request):
        qs = Document.objects.select_related('uploader').all()

        # Filtering
        case_id = request.query_params.get('case_id')
        doc_status = request.query_params.get('status')
        search = request.query_params.get('search')

        if case_id:
            qs = qs.filter(case_id__icontains=case_id)
        if doc_status:
            qs = qs.filter(status__iexact=doc_status)
        if search:
            qs = qs.filter(filename__icontains=search)

        serializer = DocumentListSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'results': serializer.data,
        })


class DocumentDetailView(APIView):
    """
    GET    /api/v1/documents/<id>/
    DELETE /api/v1/documents/<id>/
    Roles: GET → All | DELETE → ADMIN only
    """
    permission_classes = [IsAnyRole]

    def get_object(self, pk):
        try:
            return Document.objects.select_related('uploader').get(pk=pk)
        except Document.DoesNotExist:
            return None

    def get(self, request, pk):
        doc = self.get_object(pk)
        if not doc:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        log_action(
            user=request.user,
            action='VIEW',
            document=doc,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
        )
        return Response(DocumentSerializer(doc).data)

    def delete(self, request, pk):
        if not request.user.is_admin:
            return Response({'error': 'Only administrators can delete documents.'}, status=status.HTTP_403_FORBIDDEN)
        doc = self.get_object(pk)
        if not doc:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        log_action(
            user=request.user,
            action='DELETE',
            document=doc,
            result='SUCCESS',
            severity='WARNING',
            ip_address=get_client_ip(request),
            metadata={'filename': doc.filename}
        )
        doc.delete()
        return Response({'detail': 'Document deleted.'}, status=status.HTTP_200_OK)


class DocumentDownloadView(APIView):
    """
    GET /api/v1/documents/<id>/download/
    Stream the file back as a download.
    Roles: ADMIN, IO, COURT
    """
    permission_classes = [IsAnyRole]

    def get(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not doc.file or not os.path.exists(doc.file.path):
            return Response({'error': 'File not found on storage.'}, status=status.HTTP_404_NOT_FOUND)

        log_action(
            user=request.user,
            action='DOWNLOAD',
            document=doc,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={'filename': doc.filename}
        )

        response = FileResponse(
            open(doc.file.path, 'rb'),
            content_type=doc.file_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{doc.filename}"'
        response['X-Document-Hash'] = doc.sha256_hash  # Include hash in header for verification
        return response
