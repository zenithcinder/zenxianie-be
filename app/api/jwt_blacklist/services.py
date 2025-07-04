from datetime import datetime, timezone
from .models import BlacklistedToken

class TokenBlacklistService:
    @staticmethod
    def blacklist_token(token, expires_at):
        """
        Add a token to the blacklist
        """
        BlacklistedToken.objects.create(
            token=token,
            expires_at=expires_at
        )

    @staticmethod
    def is_token_blacklisted(token):
        """
        Check if a token is blacklisted
        """
        return BlacklistedToken.objects.filter(token=token).exists()

    @staticmethod
    def cleanup_expired_tokens():
        """
        Remove expired tokens from the blacklist
        """
        BlacklistedToken.objects.filter(
            expires_at__lt=datetime.now(timezone.utc)
        ).delete() 