from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import Token
import logging
import jwt
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)

class WebSocketTokenView(APIView):
    """
    API View to generate WebSocket-specific tokens for authenticated users
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Generate a WebSocket-specific token for the authenticated user"""
        try:
            user = request.user
            # Create a payload with WebSocket-specific token type
            payload = {
                'user_id': user.id,
                'email': user.email,
                'exp': datetime.now() + timedelta(days=1),  # Token valid for 1 day
                'iat': datetime.now(),
                'token_type': 'websocket'  # Specific token type for WebSocket connections
            }
            
            # Generate the WebSocket token
            ws_token = jwt.encode(
                payload,
                settings.SIMPLE_JWT['SIGNING_KEY'],
                algorithm=settings.SIMPLE_JWT['ALGORITHM']
            )
            
            logger.debug(f"Generated WebSocket token for user: {user.email}")
            
            # Return the token
            return Response({
                'access': ws_token,
                'user_id': user.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating WebSocket token: {str(e)}")
            return Response({
                'error': 'Error generating WebSocket token',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
