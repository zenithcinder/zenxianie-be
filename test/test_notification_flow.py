import os
import django
import asyncio
import json
import websockets
import requests
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')
django.setup()

User = get_user_model()

async def connect_websocket(token):
    """Connect to WebSocket with the given token"""
    uri = "ws://localhost:8000/ws/notifications/"
    async with websockets.connect(uri, subprotocols=['Bearer', token]) as websocket:
        print("Connected to WebSocket")
        return websocket

async def receive_notifications(websocket):
    """Receive and print notifications"""
    try:
        while True:
            message = await websocket.recv()
            notification = json.loads(message)
            print("\nReceived notification:")
            print(json.dumps(notification, indent=2))
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed")

def get_websocket_token(username, password):
    """Get WebSocket token using regular JWT token"""
    # First get regular JWT token
    response = requests.post(
        'http://localhost:8000/api/auth/login/',
        json={'email': username, 'password': password}
    )
    if response.status_code != 200:
        raise Exception("Failed to get regular token")
    
    regular_token = response.json()['access']
    
    # Then get WebSocket token
    response = requests.post(
        'http://localhost:8000/api/auth/token/ws/',
        headers={'Authorization': f'Bearer {regular_token}'}
    )
    if response.status_code != 200:
        raise Exception("Failed to get WebSocket token")
    
    return response.json()['access']

def send_test_notification(user_id):
    """Send a test notification to a specific user"""
    channel_layer = get_channel_layer()
    message = {
        "type": "test_notification",
        "message": "This is a test notification",
        "data": {
            "test_id": 123,
            "timestamp": datetime.now().isoformat(),
            "message": "Hello from the test script!"
        }
    }
    
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}_notifications",
        {
            "type": "notification_message",
            "message": message
        }
    )
    print(f"\nSent notification to user {user_id}")

async def main():
    print("Notification Flow Test")
    print("--------------------")
    
    # Get credentials
    username = input("Enter username (email): ")
    password = input("Enter password: ")
    
    try:
        # Get WebSocket token
        print("\nGetting WebSocket token...")
        ws_token = get_websocket_token(username, password)
        print("WebSocket token obtained successfully")
        
        # Connect to WebSocket
        print("\nConnecting to WebSocket...")
        websocket = await connect_websocket(ws_token)
        
        # Start receiving notifications in the background
        receive_task = asyncio.create_task(receive_notifications(websocket))
        
        # Get user ID to send notification to
        user_id = input("\nEnter user ID to send notification to: ")
        
        # Send test notification
        send_test_notification(int(user_id))
        
        # Wait for a few seconds to receive the notification
        print("\nWaiting for notification...")
        await asyncio.sleep(5)
        
        # Clean up
        receive_task.cancel()
        await websocket.close()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(main()) 