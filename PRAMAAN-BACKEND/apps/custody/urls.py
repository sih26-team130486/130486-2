"""
custody/urls.py
"""
from django.urls import path
from .views import (
    CustodyChainListCreateView,
    CustodyChainDetailView,
    CustodyHistoryView,
    InitiateTransferView,
    ConfirmTransferView,
    RejectTransferView,
)

urlpatterns = [
    # Chain endpoints
    path('',                            CustodyChainListCreateView.as_view(), name='custody-list-create'),
    path('<uuid:pk>/',                  CustodyChainDetailView.as_view(),     name='custody-detail'),
    path('<uuid:pk>/history/',          CustodyHistoryView.as_view(),         name='custody-history'),
    path('<uuid:pk>/transfer/',         InitiateTransferView.as_view(),       name='custody-transfer-initiate'),
    # Transfer action endpoints
    path('transfer/<uuid:t_id>/confirm/', ConfirmTransferView.as_view(),      name='custody-transfer-confirm'),
    path('transfer/<uuid:t_id>/reject/',  RejectTransferView.as_view(),       name='custody-transfer-reject'),
]
