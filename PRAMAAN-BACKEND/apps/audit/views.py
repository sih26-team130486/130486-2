"""
audit/views.py — Audit log list and detail views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.permissions import IsAdminOrIO, IsAnyRole
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(APIView):
    """
    GET /api/v1/audit/
    Returns paginated audit logs with filtering options.
    Roles: ADMIN, IO

    Query params:
      - action    : filter by action (UPLOAD, VERIFY, TAMPER_ALERT, etc.)
      - severity  : filter by severity (INFO, WARNING, CRITICAL)
      - result    : filter by result (SUCCESS, FAILED, TAMPER_DETECTED)
      - user_id   : filter by user UUID
      - doc_id    : filter by document UUID
      - case_id   : filter by case ID string
      - limit     : number of results (default 50)
    """
    permission_classes = [IsAdminOrIO]

    def get(self, request):
        qs = AuditLog.objects.select_related('user', 'document').all()

        # Filters
        action   = request.query_params.get('action')
        severity = request.query_params.get('severity')
        result   = request.query_params.get('result')
        user_id  = request.query_params.get('user_id')
        doc_id   = request.query_params.get('doc_id')
        case_id  = request.query_params.get('case_id')
        limit    = int(request.query_params.get('limit', 50))

        if action:
            qs = qs.filter(action__iexact=action)
        if severity:
            qs = qs.filter(severity__iexact=severity)
        if result:
            qs = qs.filter(result__iexact=result)
        if user_id:
            qs = qs.filter(user__id=user_id)
        if doc_id:
            qs = qs.filter(document__id=doc_id)
        if case_id:
            qs = qs.filter(case_id__icontains=case_id)

        qs = qs[:limit]
        serializer = AuditLogSerializer(qs, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
        })


class AuditLogDetailView(APIView):
    """
    GET /api/v1/audit/<id>/
    Roles: ADMIN
    """
    permission_classes = [IsAdminOrIO]

    def get(self, request, pk):
        try:
            log = AuditLog.objects.select_related('user', 'document').get(pk=pk)
        except AuditLog.DoesNotExist:
            return Response({'error': 'Audit log not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AuditLogSerializer(log).data)


class AuditStatsView(APIView):
    """
    GET /api/v1/audit/stats/
    Returns summary stats for the dashboard.
    Roles: ADMIN, IO
    """
    permission_classes = [IsAdminOrIO]

    def get(self, request):
        from django.db.models import Count
        total = AuditLog.objects.count()
        critical_count = AuditLog.objects.filter(severity='CRITICAL').count()
        tamper_count = AuditLog.objects.filter(action='TAMPER_ALERT').count()
        action_breakdown = (
            AuditLog.objects.values('action')
            .annotate(count=Count('action'))
            .order_by('-count')
        )
        return Response({
            'total_logs': total,
            'critical_alerts': critical_count,
            'tamper_alerts': tamper_count,
            'action_breakdown': list(action_breakdown),
        })
