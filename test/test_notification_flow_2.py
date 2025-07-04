import os
import django
import time
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')
django.setup()

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_test_notification(message=None, extra_data=None):
    """
    Send a test notification to all online users
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        "notifications",
        {
            "type": "send_notification",
            "content": {
                "message": message or f"Test notification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                **(extra_data or {})
            }
        }
    )

def main():
    print("Starting broadcast notification test...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Send to all online users
            send_test_notification(
                message="Broadcast test message",
                extra_data={
                    "type": "broadcast",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "test": "This is a test broadcast",
                        "count": datetime.now().strftime("%S")  # Changes every second
                    }
                }
            )
            print(f"Sent broadcast message at {datetime.now().strftime('%H:%M:%S')}")
            
            # Wait for 5 seconds before sending next message
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nStopping notification test...")

if __name__ == "__main__":
    main() 