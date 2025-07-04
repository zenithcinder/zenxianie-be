from django.urls import re_path, path
from . import consumers
from . import views
import logging

logger = logging.getLogger(__name__)

# Define WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'^ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]

# Define URL patterns for REST endpoints related to WebSockets
urlpatterns = [
    path('token/ws/', views.WebSocketTokenView.as_view(), name='websocket-token'),
]

logger.debug(f"Registered WebSocket patterns: {websocket_urlpatterns}")
logger.debug(f"Registered REST API patterns: {urlpatterns}")    