"""
redaction/urls.py
"""
from django.urls import path
from .views import (
    DetectPIIView,
    RedactDocumentView,
    RedactionJobListView,
    RedactionJobDetailView,
    DownloadRedactedFileView,
)

urlpatterns = [
    path('detect/',              DetectPIIView.as_view(),           name='redaction-detect'),
    path('redact/',              RedactDocumentView.as_view(),       name='redaction-redact'),
    path('',                     RedactionJobListView.as_view(),     name='redaction-list'),
    path('<uuid:pk>/',           RedactionJobDetailView.as_view(),   name='redaction-detail'),
    path('<uuid:pk>/download/',  DownloadRedactedFileView.as_view(), name='redaction-download'),
]
