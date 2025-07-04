from django.utils.functional import SimpleLazyObject
from django.contrib.auth.middleware import AuthenticationMiddleware
from .anonymous_user import CustomAnonymousUser
from django.contrib.auth.models import AnonymousUser

class CustomAuthenticationMiddleware(AuthenticationMiddleware):
    """
    Middleware that extends Django's AuthenticationMiddleware
    to use our CustomAnonymousUser instead of the default AnonymousUser.
    """
    
    def process_request(self, request):
        # First, let the parent middleware handle authentication
        super().process_request(request)
        
        # If the user is anonymous, replace with our CustomAnonymousUser
        if isinstance(request.user, AnonymousUser):
            request.user = CustomAnonymousUser()
            
        return None
