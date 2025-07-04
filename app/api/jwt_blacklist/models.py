from django.db import models
from django.utils.translation import gettext_lazy as _

class BlacklistedToken(models.Model):
    """Model for blacklisted JWT tokens."""
    
    token = models.TextField(_('token'), unique=True)
    blacklisted_at = models.DateTimeField(_('blacklisted at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('blacklisted token')
        verbose_name_plural = _('blacklisted tokens')
        ordering = ['-blacklisted_at']
    
    def __str__(self):
        return f"Token blacklisted at {self.blacklisted_at}"
