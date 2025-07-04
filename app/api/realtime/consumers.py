import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from channels.auth import AuthMiddlewareStack
from urllib.parse import parse_qs
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens
    """
    async def __call__(self, scope, receive, send):
        logger.debug(f"TokenAuthMiddleware called with scope: {scope}")
        
        # Get the token from subprotocols
        subprotocols = scope.get('subprotocols', [])
        logger.debug(f"Subprotocols: {subprotocols}")
        
        # Default to CustomAnonymousUser with role attribute
        from app.api.accounts.anonymous_user import CustomAnonymousUser
        scope['user'] = CustomAnonymousUser()
        
        if len(subprotocols) >= 2 and subprotocols[0] == 'Bearer':
            token = subprotocols[1]
            logger.debug(f"Token from subprotocols: {token[:10]}...")
            
            try:
                # Verify the token
                decoded_token = jwt.decode(
                    token,
                    settings.SIMPLE_JWT['SIGNING_KEY'],
                    algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
                )
                
                # Verify this is a WebSocket token
                if decoded_token.get('token_type') != 'websocket':
                    logger.warning("Token is not a WebSocket token")
                    # Continue with AnonymousUser
                else:
                    user_id = decoded_token.get('user_id')
                    logger.debug(f"Token decoded successfully for user_id: {user_id}")
                    
                    if user_id:
                        # Get the user
                        User = get_user_model()
                        try:
                            user = await database_sync_to_async(User.objects.get)(id=user_id)
                            logger.debug(f"User authenticated: {user.email}")
                            scope['user'] = user
                        except User.DoesNotExist:
                            logger.warning(f"User not found for id: {user_id}")
                            # Continue with AnonymousUser
                    
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid token: {str(e)}")
                # Continue with AnonymousUser
            except Exception as e:
                logger.error(f"Error in token authentication: {str(e)}")
                # Continue with AnonymousUser
        else:
            logger.warning("No valid token found in subprotocols")
            # Continue with AnonymousUser
            
        # Always call the parent class method to continue the middleware chain
        return await super().__call__(scope, receive, send)

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.broadcast_group_name = "notifications"

    async def connect(self):
        """Handle WebSocket connection"""
        logger.debug("Attempting WebSocket connection")
        logger.debug(f"Scope: {self.scope}")
        logger.debug(f"User: {self.scope.get('user')}")
        
        # Check if the user is authenticated (not CustomAnonymousUser)
        user = self.scope.get('user')
        
        # Accept the connection regardless of authentication status
        await self.accept()
        
        if not user or user.is_anonymous:
            logger.warning("Anonymous user connected - adding to broadcast group only")
            # Anonymous users will only receive broadcast messages, no personal notifications
            self.room_group_name = "anonymous_notifications"
            
            # Still add anonymous users to a general group for anonymous notifications
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            logger.debug(f"Added to anonymous group: {self.room_group_name}")
        else:
            logger.info(f"WebSocket connection accepted for user: {user.email}")
            
            # Add the user to their personal notification group
            user_id = getattr(user, 'id', 'anonymous')
            self.room_group_name = f"user_{user_id}_notifications"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            logger.debug(f"Added to group: {self.room_group_name}")

        # Add the user to the broadcast group
        await self.channel_layer.group_add(
            self.broadcast_group_name,
            self.channel_name
        )
        logger.debug(f"Added to broadcast group: {self.broadcast_group_name}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.debug(f"WebSocket disconnecting with code: {close_code}")
        if hasattr(self, 'room_group_name') and self.room_group_name is not None:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.debug(f"Removed from group: {self.room_group_name}")
        
        # Remove from broadcast group
        await self.channel_layer.group_discard(
            self.broadcast_group_name,
            self.channel_name
        )
        logger.debug(f"Removed from broadcast group: {self.broadcast_group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages"""
        if text_data:
            logger.debug(f"Received text message: {text_data}")
            try:
                text_data_json = json.loads(text_data)
                message = text_data_json.get('message', '')
                
                user = self.scope.get('user')
                if user and not user.is_anonymous:
                    logger.info(f"Received message from {user.email}: {message}")
                else:
                    logger.info(f"Received message from anonymous user: {message}")
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
                return
        elif bytes_data:
            logger.debug(f"Received binary message: {bytes_data}")

    async def send_notification(self, event):
        """Handle notification messages from the channel layer"""
        logger.debug(f"Received notification: {event}")
        content = event.get('content', {})
        await self.send(text_data=json.dumps(content))
        logger.debug("Notification sent to client") 