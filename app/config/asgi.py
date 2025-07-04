"""
ASGI config for zenxianie Backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django
import logging
import threading
import time
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Set the Django settings module path before importing any Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Django
django.setup()

# Now we can safely import Django and app-specific modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from app.api.realtime.consumers import TokenAuthMiddleware
import app.api.realtime.routing

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

def run_notification_test():
    """Run the notification test in a separate thread"""
    logger.info("Starting notification test thread")
    def send_notification():
        while True:
            print("Sending notification👈👈👈👈")
            try:
                channel_layer = get_channel_layer()
                logger.info("Attempting to send notification...")
                # Send to all connected users
                async_to_sync(channel_layer.group_send)(
                    "notifications",  # Broadcast group
                    {
                        "type": "send_notification",  # Changed to match the consumer method
                        "content": {  # Changed to match the expected format
                            "type": "broadcast",
                            "message": "Broadcast test message",
                            "timestamp": datetime.now().isoformat(),
                            "data": {
                                "test": "This is a test broadcast",
                                "count": datetime.now().strftime("%S")
                            }
                        }
                    }
                )
                logger.info(f"Successfully sent broadcast message at {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in notification test: {str(e)}")
                logger.exception("Full traceback:")
                time.sleep(5)

    # Start the notification test in a separate thread
    notification_thread = threading.Thread(target=send_notification, daemon=True)
    notification_thread.start()
    logger.info("Notification test thread started")

async def lifespan(scope, receive, send):
    """Handle ASGI lifespan protocol"""
    logger.info("Lifespan protocol started")
    if scope["type"] == "lifespan":
        logger.info("Processing lifespan messages")
        while True:
            message = await receive()
            logger.info(f"Received lifespan message: {message['type']}")
            
            if message["type"] == "lifespan.startup":
                logger.info("Starting notification test on application startup")
                run_notification_test()
                await send({"type": "lifespan.startup.complete"})
                logger.info("Lifespan startup complete")
            elif message["type"] == "lifespan.shutdown":
                logger.info("Processing lifespan shutdown")
                await send({"type": "lifespan.shutdown.complete"})
                logger.info("Lifespan shutdown complete")
                return

# Create the ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "lifespan": lifespan,
    "websocket": TokenAuthMiddleware(
        URLRouter(
            app.api.realtime.routing.websocket_urlpatterns
        )
    ),
})

# Start the notification test when the application is initialized
# run_notification_test()

logger.info("ASGI application initialized with WebSocket routing") 