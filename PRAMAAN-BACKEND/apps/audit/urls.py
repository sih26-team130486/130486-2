"""
audit/urls.py
"""
from django.urls import path
from .views import AuditLogListView, AuditLogDetailView, AuditStatsView

urlpatterns = [
    path('',           AuditLogListView.as_view(),   name='audit-list'),
    path('stats/',     AuditStatsView.as_view(),     name='audit-stats'),
    path('<uuid:pk>/', AuditLogDetailView.as_view(), name='audit-detail'),
]
