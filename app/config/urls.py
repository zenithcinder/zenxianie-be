from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from app.api.realtime.routing import websocket_urlpatterns, urlpatterns as realtime_urlpatterns

schema_view = get_schema_view(
    openapi.Info(
        title="Zenxianie API",
        default_version='v1',
        description="API documentation for the Zenxianie application.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@zenxianie.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),  # Django admin with trailing slash
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0)),
      # Authentication
    path('api/auth/', include([
        path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('refresh-token/', TokenRefreshView.as_view()),
        path('', include('app.api.jwt_blacklist.urls')),
        path('', include('app.api.accounts.urls')),
        path('', include(realtime_urlpatterns)),  # Include WebSocket token endpoint
    ])),
    
    # User endpoints
    path('api/user/', include([
        path('', include('app.api.reservations.urls')),
        path('', include('app.api.parking_lots.urls')),
        path('', include('app.api.notification.urls')),
        path('', include('app.api.payments.urls')),  # Add payment endpoints
    ])),

    # Admin API endpoints (changed from admin-api to api/admin)
    path('api/admin/', include([
        path('', include('app.api.accounts.urls')),
        path('', include('app.api.parking_lots.urls')),
        path('', include('app.api.reservations.urls')),
        path('', include('app.api.reports.urls')),
        path('', include('app.api.payments.urls')),  # Add payment endpoints for admin
    ])),
]

# Add WebSocket URL patterns
urlpatterns += websocket_urlpatterns

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)