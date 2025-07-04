import os
import django
import asyncio
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')
django.setup()

User = get_user_model()

def send_notification(user_id, message):
    """
    Send a notification to a specific user by their ID
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}_notifications",
        {
            "type": "notification_message",
            "message": message
        }
    )

def send_notification_by_username(username, message):
    """
    Send a notification to a specific user by their username/email
    """
    try:
        user = User.objects.get(email=username)
        send_notification(user.id, message)
        return True
    except User.DoesNotExist:
        print(f"User with username {username} not found")
        return False

def main():
    # Example usage
    print("Notification Test Script")
    print("----------------------")
    
    # Get user input
    user_input = input("Enter user ID or email to send notification to: ")
    
    # Try to convert to integer (user ID)
    try:
        user_id = int(user_input)
        # Send notification by ID
        message = {
            "type": "test_notification",
            "message": "This is a test notification",
            "data": {
                "test_id": 123,
                "timestamp": "2024-03-06T12:00:00Z"
            }
        }
        send_notification(user_id, message)
        print(f"Notification sent to user ID: {user_id}")
    except ValueError:
        # If not an integer, treat as email/username
        message = {
            "type": "test_notification",
            "message": "This is a test notification",
            "data": {
                "test_id": 123,
                "timestamp": "2024-03-06T12:00:00Z"
            }
        }
        if send_notification_by_username(user_input, message):
            print(f"Notification sent to user: {user_input}")

if __name__ == "__main__":
    main() 