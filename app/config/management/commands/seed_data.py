from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.api.parking_lots.models import ParkingLot, ParkingSpace
from app.api.reservations.models import Reservation
from app.api.reports.models import DailyReport, MonthlyReport, ParkingLotReport
from django.utils import timezone
from datetime import timedelta, datetime
import random
from decimal import Decimal
from django.db import connection

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with sample data'

    def reset_database(self):
        """Reset the database by dropping all data and resetting sequences."""
        self.stdout.write('Resetting database...')
        
        with connection.cursor() as cursor:
            # Disable foreign key constraints temporarily
            cursor.execute('SET CONSTRAINTS ALL DEFERRED')
            
            # Get all tables in the database
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            tables = cursor.fetchall()
            
            # Drop all data from tables
            for table in tables:
                table_name = table[0]
                if table_name != 'django_migrations':  # Skip migrations table
                    self.stdout.write(f'Dropping data from {table_name}...')
                    cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE')
            
            # Reset all sequences
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public'
            """)
            sequences = cursor.fetchall()
            
            for sequence in sequences:
                sequence_name = sequence[0]
                self.stdout.write(f'Resetting sequence {sequence_name}...')
                cursor.execute(f'ALTER SEQUENCE "{sequence_name}" RESTART WITH 1')
            
            # Re-enable foreign key constraints
            cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')
            
        self.stdout.write(self.style.SUCCESS('Database reset complete'))

    def handle(self, *args, **options):
        # Reset the database first
        self.reset_database()
        
        self.stdout.write('Seeding new data...')

        # Create admin user
        admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='admin123',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create regular users with more realistic data
        users = []
        user_data = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com'},
            {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com'},
            {'first_name': 'Michael', 'last_name': 'Johnson', 'email': 'michael.j@example.com'},
            {'first_name': 'Sarah', 'last_name': 'Williams', 'email': 'sarah.w@example.com'},
            {'first_name': 'David', 'last_name': 'Brown', 'email': 'david.b@example.com'},
        ]

        for user_info in user_data:
            user = User.objects.create_user(
                email=user_info['email'],
                username=user_info['email'].split('@')[0],
                password='user123',
                first_name=user_info['first_name'],
                last_name=user_info['last_name'],
                role='user',
                is_staff=False,
                is_superuser=False
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS('Created regular users'))

        # Create parking lots with more realistic data
        parking_lots = []
        locations = [
            {
                'name': 'Amsterdam Centraal',
                'lat': 52.3780,
                'lng': 4.9000,
                'address': 'Stationsplein, 1012 AB Amsterdam, Netherlands',
                'total_spaces': 500,
                'hourly_rate': 5.00
            },
            {
                'name': 'Rotterdam Blaak',
                'lat': 51.9225,
                'lng': 4.4886,
                'address': 'Blaak 1, 3011 GA Rotterdam, Netherlands',
                'total_spaces': 300,
                'hourly_rate': 4.50
            },
            {
                'name': 'Utrecht Centraal',
                'lat': 52.0894,
                'lng': 5.1106,
                'address': 'Stationshal 12, 3511 CE Utrecht, Netherlands',
                'total_spaces': 400,
                'hourly_rate': 4.00
            },
            {
                'name': 'Den Haag HS',
                'lat': 52.0705,
                'lng': 4.3170,
                'address': 'Stationsplein 41, 2515 BT Den Haag, Netherlands',
                'total_spaces': 350,
                'hourly_rate': 3.50
            },
            {
                'name': 'Eindhoven Station',
                'lat': 51.4416,
                'lng': 5.4697,
                'address': 'Stationsplein 22, 5611 AC Eindhoven, Netherlands',
                'total_spaces': 250,
                'hourly_rate': 3.00
            },
        ]

        for loc in locations:
            # Calculate available spaces (random between 20% and 80% of total)
            available_spaces = random.randint(
                int(loc['total_spaces'] * 0.2),
                int(loc['total_spaces'] * 0.8)
            )
            
            lot = ParkingLot.objects.create(
                name=loc['name'],
                latitude=Decimal(str(loc['lat'])),
                longitude=Decimal(str(loc['lng'])),
                address=loc['address'],
                total_spaces=loc['total_spaces'],
                available_spaces=available_spaces,
                status=ParkingLot.Status.ACTIVE,
                hourly_rate=Decimal(str(loc['hourly_rate']))
            )
            parking_lots.append(lot)
        self.stdout.write(self.style.SUCCESS('Created parking lots'))

        # Create parking spaces for each lot
        for lot in parking_lots:
            # Get a short prefix from the lot name (first 3 letters)
            prefix = lot.name[:3].upper()
            
            # Calculate how many spaces should be available
            available_count = lot.available_spaces
            total_count = lot.total_spaces
            
            for i in range(total_count):
                # Calculate if space should be available
                should_be_available = i < available_count
                
                ParkingSpace.objects.create(
                    parking_lot=lot,
                    space_number=f"{prefix}{i+1:03d}",  # Format: "SMC001", "ABR001", etc.
                    status=ParkingSpace.Status.AVAILABLE if should_be_available else ParkingSpace.Status.OCCUPIED
                )
        self.stdout.write(self.style.SUCCESS('Created parking spaces'))

        # Create reservations with more realistic data
        total_reservations = 0
        vehicle_plates = [
            'ABC123', 'XYZ789', 'DEF456', 'GHI789', 'JKL012',
            'MNO345', 'PQR678', 'STU901', 'VWX234', 'YZA567'
        ]
        
        # Generate reservations for the last 30 days
        for day in range(30):
            current_date = timezone.now().date() - timedelta(days=day)
            
            for user in users:
                reservations_per_user = random.randint(1, 3)  # Random number of reservations per user
                while reservations_per_user > 0:
                    lot = random.choice(parking_lots)
                    # Get an available parking space from the lot
                    available_spaces = ParkingSpace.objects.filter(
                        parking_lot=lot,
                        status=ParkingSpace.Status.AVAILABLE
                    )
                    
                    if not available_spaces.exists():
                        self.stdout.write(self.style.WARNING(f'No available spaces in {lot.name}, skipping...'))
                        break
                    
                    space = random.choice(list(available_spaces))
                    
                    # Generate realistic reservation times
                    start_time = timezone.make_aware(datetime.combine(
                        current_date,
                        datetime.strptime(f"{random.randint(6, 20)}:{random.choice(['00', '15', '30', '45'])}", "%H:%M").time()
                    ))
                    duration = random.randint(1, 8)  # Random duration between 1 and 8 hours
                    end_time = start_time + timedelta(hours=duration)
                    
                    try:
                        Reservation.objects.create(
                            parking_lot=lot,
                            parking_space=space,
                            user=user,
                            vehicle_plate=random.choice(vehicle_plates),
                            start_time=start_time,
                            end_time=end_time,
                            status='completed',  # Set as completed for historical data
                            notes=f"Reservation for {user.get_full_name()}"
                        )
                        reservations_per_user -= 1
                        total_reservations += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error creating reservation: {str(e)}'))
                        break

        self.stdout.write(self.style.SUCCESS(f'Created {total_reservations} reservations'))

        # Generate reports with more comprehensive data
        self.stdout.write('Generating reports...')
        
        # Generate daily reports for the next 30 days (future dates)
        for day in range(30):
            current_date = timezone.now().date() + timedelta(days=day+1)  # Start from tomorrow
            
            # Generate daily report using the model's method
            DailyReport.generate_report(date=current_date)
            
            # Generate parking lot reports for each lot
            for lot in parking_lots:
                ParkingLotReport.generate_report(parking_lot=lot, date=current_date)
        
        # Generate monthly reports for the next 12 months
        current_date = timezone.now().date()
        for month_offset in range(12):
            target_date = current_date + timedelta(days=30 * month_offset)  # Future months
            year = target_date.year
            month = target_date.month
            
            # Generate monthly report using the model's method
            MonthlyReport.generate_report(year=year, month=month)
        
        self.stdout.write(self.style.SUCCESS('Successfully generated reports'))
        self.stdout.write(self.style.SUCCESS('Successfully seeded data')) 