"""
PRAMAAN — Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/auth/',         include('apps.accounts.urls')),
    path('api/v1/documents/',    include('apps.documents.urls')),
    path('api/v1/verification/', include('apps.verification.urls')),
    path('api/v1/audit/',        include('apps.audit.urls')),
    path('api/v1/custody/',      include('apps.custody.urls')),
    path('api/v1/certificates/', include('apps.certificates.urls')),
    path('api/v1/redaction/',    include('apps.redaction.urls')),
    path('api/v1/search/',       include('apps.search.urls')),
    path('api-auth/',            include('rest_framework.urls')),
]

# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
