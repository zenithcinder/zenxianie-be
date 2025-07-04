#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
import time
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def run_notification_test():
    print("Running notification test")
    """Run the notification test in a separate thread"""
    def send_notification():
        while True:
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "send_notification",
                        "content": {
                            "message": "Broadcast test message",
                            "type": "broadcast",
                            "timestamp": datetime.now().isoformat(),
                            "data": {
                                "test": "This is a test broadcast",
                                "count": datetime.now().strftime("%S")
                            }
                        }
                    }
                )
                print(f"Sent broadcast message at {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(5)
            except Exception as e:
                print(f"Error in notification test: {e}")
                time.sleep(5)

    # Start the notification test in a separate thread
    notification_thread = threading.Thread(target=send_notification, daemon=True)
    notification_thread.start()

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Start notification test if running the server
    if len(sys.argv) > 1 and sys.argv[1] in ['runserver', 'runserver_plus']:
        run_notification_test()
    
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
