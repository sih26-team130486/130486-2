"""
redaction/apps.py
"""
from django.apps import AppConfig


class RedactionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name  = 'apps.redaction'
    label = 'redaction'
    verbose_name = 'PII Redaction'
