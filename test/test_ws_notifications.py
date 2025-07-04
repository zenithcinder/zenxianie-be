import asyncio
import websockets
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_http_get():
    """This will fail with 404 because it's not a WebSocket connection"""
    try:
        response = requests.get("http://localhost:8000/ws/notifications/")
        print("HTTP Response:", response.status_code)
    except Exception as e:
        print("HTTP GET failed:", e)

def get_auth_token():
    """Get JWT token for authentication"""
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login/",
            json={
                "email": "john.doe@example.com",
                "password": "user123"
            }
        )
        if response.status_code == 200:
            token = response.json().get('access')
            logger.debug(f"Got auth token: {token[:10]}...")
            return token
        else:
            logger.error(f"Failed to get auth token: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting auth token: {e}")
        return None

async def test_websocket():
    """Test WebSocket connection with authentication"""
    token = get_auth_token()
    if not token:
        logger.error("Could not get authentication token")
        return

    # WebSocket URL with ws/ prefix
    uri = "ws://localhost:8000/ws/notifications/"
    logger.debug(f"Connecting to WebSocket at: {uri}")
    
    try:
        # Create connection with authorization header
        async with websockets.connect(
            uri,
            subprotocols=["Bearer", token]  # Use subprotocols for auth
        ) as websocket:
            logger.info("WebSocket Connected Successfully!")
            response = await websocket.recv()
            logger.info(f"Received: {response}")
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WebSocket connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    print("Testing HTTP GET (this will fail):")
    test_http_get()
    print("\nTesting WebSocket with authentication:")
    asyncio.run(test_websocket()) 