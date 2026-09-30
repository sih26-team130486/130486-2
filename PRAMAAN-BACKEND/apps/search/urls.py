"""
search/urls.py
"""
from django.urls import path
from .views import DocumentSearchView

urlpatterns = [
    path('documents/', DocumentSearchView.as_view(), name='document-search'),
]
