from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Checks and fixes admin users'

    def handle(self, *args, **options):
        # Get all users with role='admin'
        admin_users = User.objects.filter(role='admin')
        
        if not admin_users.exists():
            self.stdout.write(self.style.WARNING('No admin users found!'))
            return
            
        for user in admin_users:
            self.stdout.write(f'Checking user: {user.username}')
            self.stdout.write(f'is_staff: {user.is_staff}')
            self.stdout.write(f'is_superuser: {user.is_superuser}')
            
            if not user.is_staff:
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Fixed {user.username}: set is_staff=True'))
            
            if not user.is_superuser:
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Fixed {user.username}: set is_superuser=True')) 