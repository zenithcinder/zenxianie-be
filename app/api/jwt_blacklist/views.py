from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import BlacklistedToken

# Create your views here.

class LogoutView(APIView):
    """View for logging out users and blacklisting their tokens."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Blacklist the refresh token and return success response."""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'detail': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Store the blacklisted token in our database
            BlacklistedToken.objects.create(token=refresh_token)
            
            return Response(
                {'detail': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class LogoutAllView(APIView):
    """View for logging out users from all devices."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Blacklist all refresh tokens for the user."""
        try:
            # Get all refresh tokens for the user
            tokens = RefreshToken.objects.filter(user=request.user)
            
            # Blacklist all tokens
            for token in tokens:
                token.blacklist()
                BlacklistedToken.objects.create(token=str(token))
            
            return Response(
                {'detail': 'Successfully logged out from all devices.'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
