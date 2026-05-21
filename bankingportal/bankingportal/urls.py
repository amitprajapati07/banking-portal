"""Root URL configuration for the banking portal project."""

from django.contrib import admin
from django.urls import include, path
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        "status": "active",
        "message": "Banking Portal API is operational",
        "version": "1.0.0",
        "docs": {
            "swagger": "/api/schema/swagger-ui/",
            "redoc": "/api/schema/redoc/",
            "schema": "/api/schema/"
        }
    })

urlpatterns = [
    path("", api_root),
    path("admin/", admin.site.urls),
    # Swagger/Redoc endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path(
        "api/v1/",
        include(
            [
                # Auth + User profile endpoints (both live in user_profiles app)
                path("", include("apps.user_profiles.urls")),
                # Account endpoints
                path("accounts/", include("apps.accounts.urls")),
                # Transaction endpoints
                path("transactions/", include("apps.transactions.urls")),
            ]
        ),
    ),
]
