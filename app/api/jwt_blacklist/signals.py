from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework_simplejwt.tokens import RefreshToken
from .services import TokenBlacklistService

@receiver(post_save, sender=RefreshToken)
def blacklist_refresh_token(sender, instance, created, **kwargs):
    """
    Automatically blacklist refresh tokens when they are rotated
    """
    if not created and instance.blacklisted_at:
        TokenBlacklistService.blacklist_token(
            str(instance),
            instance.expires_at
        ) 