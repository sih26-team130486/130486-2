"""
custody/views.py — Chain of Custody REST API

Endpoints:
  POST   /api/v1/custody/                        Register evidence into custody chain
  GET    /api/v1/custody/                        List all chains
  GET    /api/v1/custody/<id>/                   Custody chain detail + full history
  POST   /api/v1/custody/<id>/transfer/          Initiate a transfer (IO -> CFSL / Court)
  GET    /api/v1/custody/<id>/history/           Chronological transfer history
  POST   /api/v1/custody/transfer/<t_id>/confirm/  Receiver confirms receipt
  POST   /api/v1/custody/transfer/<t_id>/reject/   Receiver rejects transfer
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.models import CustomUser
from apps.accounts.permissions import IsAdminOrIO, IsAnyRole
from apps.audit.utils import log_action
from apps.documents.models import Document
from .models import CustodyChain, CustodyTransfer
from .serializers import (
    CustodyChainSerializer, CustodyChainListSerializer,
    CustodyTransferSerializer, InitiateTransferSerializer,
)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


# ---------------------------------------------------------------------------
# Register + List
# ---------------------------------------------------------------------------
class CustodyChainListCreateView(APIView):
    """
    GET  /api/v1/custody/  — List all chains
    POST /api/v1/custody/  — Register a document into custody chain
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminOrIO()]
        return [IsAnyRole()]

    def get(self, request):
        qs = CustodyChain.objects.select_related('document', 'current_holder').all()
        # Filter
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status__iexact=status_filter)
        serializer = CustodyChainListSerializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})

    def post(self, request):
        doc_id  = request.data.get('document_id')
        location = request.data.get('location', '')

        if not doc_id:
            return Response({'error': 'document_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doc = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(doc, 'custody_chain'):
            return Response(
                {'error': 'This document already has a custody chain.',
                 'custody_chain_id': str(doc.custody_chain.id)},
                status=status.HTTP_400_BAD_REQUEST
            )

        chain = CustodyChain.objects.create(
            document         = doc,
            current_holder   = request.user,
            current_location = location,
            status           = 'REGISTERED',
        )

        log_action(
            user=request.user,
            action='CUSTODY_TRANSFER',
            document=doc,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={'event': 'REGISTERED', 'location': location, 'chain_id': str(chain.id)}
        )

        return Response(CustodyChainSerializer(chain).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Detail + History
# ---------------------------------------------------------------------------
class CustodyChainDetailView(APIView):
    """GET /api/v1/custody/<id>/  — Full chain detail with all transfers."""
    permission_classes = [IsAnyRole]

    def get_object(self, pk):
        try:
            return CustodyChain.objects.select_related(
                'document', 'current_holder'
            ).prefetch_related('transfers__from_user', 'transfers__to_user').get(pk=pk)
        except CustodyChain.DoesNotExist:
            return None

    def get(self, request, pk):
        chain = self.get_object(pk)
        if not chain:
            return Response({'error': 'Custody chain not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CustodyChainSerializer(chain).data)


class CustodyHistoryView(APIView):
    """GET /api/v1/custody/<id>/history/  — Chronological transfer timeline."""
    permission_classes = [IsAnyRole]

    def get(self, request, pk):
        try:
            chain = CustodyChain.objects.select_related('document', 'current_holder').get(pk=pk)
        except CustodyChain.DoesNotExist:
            return Response({'error': 'Custody chain not found.'}, status=status.HTTP_404_NOT_FOUND)

        transfers = CustodyTransfer.objects.filter(
            custody_chain=chain
        ).select_related('from_user', 'to_user').order_by('initiated_at')

        return Response({
            'chain_id':        str(chain.id),
            'document':        chain.document.filename,
            'current_holder':  chain.current_holder.full_name if chain.current_holder else '—',
            'current_status':  chain.get_status_display(),
            'transfer_count':  transfers.count(),
            'history':         CustodyTransferSerializer(transfers, many=True).data,
        })


# ---------------------------------------------------------------------------
# Initiate Transfer
# ---------------------------------------------------------------------------
class InitiateTransferView(APIView):
    """
    POST /api/v1/custody/<id>/transfer/
    IO initiates a handover to another user (CFSL officer / Court).
    Creates a PENDING transfer. Receiver must confirm.
    """
    permission_classes = [IsAdminOrIO]

    def post(self, request, pk):
        try:
            chain = CustodyChain.objects.select_related('document', 'current_holder').get(pk=pk)
        except CustodyChain.DoesNotExist:
            return Response({'error': 'Custody chain not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only current holder can initiate transfer
        if chain.current_holder != request.user and not request.user.is_admin:
            return Response(
                {'error': 'Only the current holder can initiate a transfer.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Block if a transfer is already PENDING
        if chain.transfers.filter(status='PENDING').exists():
            return Response(
                {'error': 'A transfer is already pending confirmation. Confirm or reject it first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InitiateTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vdata = serializer.validated_data

        try:
            to_user = CustomUser.objects.get(pk=vdata['to_user_id'])
        except CustomUser.DoesNotExist:
            return Response({'error': 'Recipient user not found.'}, status=status.HTTP_404_NOT_FOUND)

        if to_user == request.user:
            return Response({'error': 'Cannot transfer to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        # Snapshot the current hash at transfer time
        transfer = CustodyTransfer.objects.create(
            custody_chain             = chain,
            from_user                 = request.user,
            to_user                   = to_user,
            from_location             = chain.current_location,
            to_location               = vdata['to_location'],
            transfer_reason           = vdata.get('transfer_reason', ''),
            notes                     = vdata.get('notes', ''),
            status                    = 'PENDING',
            document_hash_at_transfer = chain.document.sha256_hash,
        )

        # Update chain status
        chain.status = 'IN_TRANSFER'
        chain.save(update_fields=['status', 'updated_at'])

        log_action(
            user=request.user,
            action='CUSTODY_TRANSFER',
            document=chain.document,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={
                'event': 'TRANSFER_INITIATED',
                'to_user': to_user.username,
                'to_location': vdata['to_location'],
                'transfer_id': str(transfer.id),
                'hash_snapshot': chain.document.sha256_hash,
            }
        )

        return Response({
            'message': f'Transfer initiated to {to_user.full_name}. Awaiting confirmation.',
            'transfer': CustodyTransferSerializer(transfer).data,
        }, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Confirm Transfer
# ---------------------------------------------------------------------------
class ConfirmTransferView(APIView):
    """
    POST /api/v1/custody/transfer/<t_id>/confirm/
    Receiver confirms physical receipt of the evidence.
    Chain status updated, current_holder changes to receiver.
    """
    permission_classes = [IsAdminOrIO]

    def post(self, request, t_id):
        try:
            transfer = CustodyTransfer.objects.select_related(
                'custody_chain__document', 'custody_chain__current_holder',
                'from_user', 'to_user'
            ).get(pk=t_id)
        except CustodyTransfer.DoesNotExist:
            return Response({'error': 'Transfer record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if transfer.status != 'PENDING':
            return Response(
                {'error': f'Transfer is already {transfer.get_status_display()}. Cannot confirm again.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only the intended recipient or admin can confirm
        if transfer.to_user != request.user and not request.user.is_admin:
            return Response(
                {'error': 'Only the intended recipient can confirm this transfer.'},
                status=status.HTTP_403_FORBIDDEN
            )

        notes = request.data.get('notes', '')

        # Confirm the transfer
        transfer.status       = 'CONFIRMED'
        transfer.confirmed_at = timezone.now()
        if notes:
            transfer.notes = notes
        transfer.save(update_fields=['status', 'confirmed_at', 'notes'])

        # Update chain — new holder is the receiver
        chain = transfer.custody_chain
        chain.current_holder   = transfer.to_user
        chain.current_location = transfer.to_location

        # Determine new chain status
        if transfer.to_user.role == 'COURT':
            chain.status = 'WITH_COURT'
        else:
            chain.status = 'WITH_CFSL'
        chain.save(update_fields=['current_holder', 'current_location', 'status', 'updated_at'])

        log_action(
            user=request.user,
            action='CUSTODY_TRANSFER',
            document=chain.document,
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={
                'event': 'TRANSFER_CONFIRMED',
                'from_user': transfer.from_user.username if transfer.from_user else '?',
                'transfer_id': str(transfer.id),
                'new_location': transfer.to_location,
            }
        )

        return Response({
            'message': f'Transfer confirmed. Evidence now with {request.user.full_name}.',
            'transfer': CustodyTransferSerializer(transfer).data,
        })


# ---------------------------------------------------------------------------
# Reject Transfer
# ---------------------------------------------------------------------------
class RejectTransferView(APIView):
    """
    POST /api/v1/custody/transfer/<t_id>/reject/
    Receiver rejects — chain reverts to previous holder.
    """
    permission_classes = [IsAdminOrIO]

    def post(self, request, t_id):
        try:
            transfer = CustodyTransfer.objects.select_related(
                'custody_chain__document', 'from_user', 'to_user'
            ).get(pk=t_id)
        except CustodyTransfer.DoesNotExist:
            return Response({'error': 'Transfer record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if transfer.status != 'PENDING':
            return Response(
                {'error': f'Transfer is already {transfer.get_status_display()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if transfer.to_user != request.user and not request.user.is_admin:
            return Response(
                {'error': 'Only the intended recipient can reject this transfer.'},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get('reason', 'No reason provided.')
        transfer.status = 'REJECTED'
        transfer.notes  = reason
        transfer.save(update_fields=['status', 'notes'])

        # Revert chain to REGISTERED
        chain = transfer.custody_chain
        chain.status = 'REGISTERED'
        chain.save(update_fields=['status', 'updated_at'])

        log_action(
            user=request.user,
            action='CUSTODY_TRANSFER',
            document=chain.document,
            result='FAILED',
            severity='WARNING',
            ip_address=get_client_ip(request),
            metadata={
                'event': 'TRANSFER_REJECTED',
                'reason': reason,
                'transfer_id': str(transfer.id),
            }
        )

        return Response({
            'message': 'Transfer rejected. Chain reverted to previous holder.',
            'transfer': CustodyTransferSerializer(transfer).data,
        })
