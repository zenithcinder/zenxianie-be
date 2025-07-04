import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import psycopg2

class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        while not db_conn:
            try:
                # Try to connect to the database
                db_conn = connections['default']
                # Test the connection
                db_conn.cursor()
                self.stdout.write(self.style.SUCCESS('Database available!'))
                return
            except (OperationalError, psycopg2.OperationalError) as e:
                self.stdout.write(self.style.WARNING(f'Database unavailable, waiting 1 second... ({str(e)})'))
                time.sleep(1) 