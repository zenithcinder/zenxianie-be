from django.core.management.base import BaseCommand
from jwt_blacklist.services import TokenBlacklistService

class Command(BaseCommand):
    help = 'Clean up expired tokens from the blacklist'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning up expired tokens...')
        TokenBlacklistService.cleanup_expired_tokens()
        self.stdout.write(self.style.SUCCESS('Successfully cleaned up expired tokens')) 