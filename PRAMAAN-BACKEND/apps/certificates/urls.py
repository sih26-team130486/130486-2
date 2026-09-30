"""
certificates/urls.py
"""
from django.urls import path
from .views import (
    GenerateCertificateView,
    CertificateListView,
    CertificateDetailView,
    CertificateDownloadView,
)

urlpatterns = [
    path('generate/',             GenerateCertificateView.as_view(),  name='cert-generate'),
    path('',                      CertificateListView.as_view(),      name='cert-list'),
    path('<uuid:pk>/',            CertificateDetailView.as_view(),    name='cert-detail'),
    path('<uuid:pk>/download/',   CertificateDownloadView.as_view(),  name='cert-download'),
]
