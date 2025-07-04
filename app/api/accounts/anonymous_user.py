from django.contrib.auth.models import AnonymousUser

class CustomAnonymousUser(AnonymousUser):
    """
    Extended AnonymousUser class that includes attributes required by API endpoints.
    This prevents Swagger and other APIs from throwing errors about missing attributes.
    """
    
    # Define Role class to mimic User.Role for consistency
    class Role:
        USER = "user"
        ADMIN = "admin"
        ANONYMOUS = "anonymous"
    
    @property
    def role(self):
        """
        Returns 'anonymous' as the default role for unauthenticated users.
        This makes APIs expecting a 'role' attribute work with anonymous users.
        """
        return self.Role.ANONYMOUS
    
    # This is important for role comparisons like user.role == User.Role.ADMIN
    def __eq__(self, other):
        if isinstance(other, str):
            return self.role == other
        return super().__eq__(other)
    
    def __init__(self):
        super().__init__()
        self._is_admin = False
        self._created_at = None
        self._updated_at = None
        self._avatar_url = ''
    
    # Add standard model properties
    @property
    def status(self):
        return 'inactive'
    
    @property
    def id(self):
        """
        Return None for id to avoid type errors when code expects user.id to be a number.
        This prevents errors when passing the AnonymousUser where a User model is expected.
        """
        return None
        
    # Override pk property as well, which is often used as an alias for id
    @property
    def pk(self):
        return None
    
    # User model specific properties
    @property
    def is_admin(self):
        return False
    
    @property
    def avatar_url(self):
        return ''
    
    @property
    def created_at(self):
        return None
    
    @property
    def updated_at(self):
        return None
    
    def get_full_name(self):
        return "Anonymous User"
