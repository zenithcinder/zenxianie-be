from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import BlacklistedToken

class BlacklistJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that checks for blacklisted tokens."""
    
    def authenticate(self, request):
        """Authenticate the request and check if the token is blacklisted."""
        try:
            # Get the token from the request
            header = self.get_header(request)
            if header is None:
                return None
            
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None
            
            # Check if the token is blacklisted
            if BlacklistedToken.objects.filter(token=raw_token.decode()).exists():
                raise InvalidToken('Token has been blacklisted')
            
            # Validate the token
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
            
        except TokenError as e:
            raise InvalidToken(e.args[0]) 