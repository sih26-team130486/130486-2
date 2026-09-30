"""
verification/urls.py
"""
from django.urls import path
from .views import VerifyDocumentView, VerificationListView, VerificationDetailView

urlpatterns = [
    path('',                           VerificationListView.as_view(),   name='verification-list'),
    path('<uuid:pk>/',                 VerificationDetailView.as_view(), name='verification-detail'),
    path('<uuid:doc_id>/verify/',      VerifyDocumentView.as_view(),     name='document-verify'),
]
