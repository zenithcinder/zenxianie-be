from django.contrib.auth import get_user_model
from app.api.parking_lots.models import ParkingLot, ParkingSpace
from app.api.reservations.models import Reservation
from app.api.reports.models import DailyReport, MonthlyReport, ParkingLotReport
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import factory
from factory.django import DjangoModelFactory

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'user'
    status = 'active'
    is_active = True

class AdminUserFactory(UserFactory):
    role = 'admin'
    is_staff = True
    is_superuser = True

class ParkingLotUserOwnedFactory(DjangoModelFactory):
    class Meta:
        model = ParkingLot

    name = factory.Sequence(lambda n: f'Parking Lot {n}')
    address = factory.Faker('address')
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')
    total_spaces = 50
    available_spaces = 50
    hourly_rate = Decimal('10.00')
    owner = factory.SubFactory(UserFactory,role='user', is_staff=False, is_superuser=False)
    status = ParkingLot.Status.ACTIVE

class ParkingSpaceFactory(DjangoModelFactory):
    class Meta:
        model = ParkingSpace

    parking_lot = factory.SubFactory(ParkingLotUserOwnedFactory)
    space_number = factory.Sequence(lambda n: f'A{n}')
    status = ParkingSpace.Status.AVAILABLE

class ReservationFactory(DjangoModelFactory):
    class Meta:
        model = Reservation

    user = factory.SubFactory(UserFactory)
    parking_lot = factory.SubFactory(ParkingLotUserOwnedFactory)
    parking_space = factory.SubFactory(ParkingSpaceFactory)
    vehicle_plate = factory.Sequence(lambda n: f'ABC{n:03d}')
    start_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    end_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=3))
    status = Reservation.Status.ACTIVE
    notes = factory.Faker('text', max_nb_chars=200)

class DailyReportFactory(DjangoModelFactory):
    class Meta:
        model = DailyReport

    date = factory.Sequence(lambda n: (datetime.now() - timedelta(days=n+1)).date())
    total_revenue = Decimal('1000.00')
    total_reservations = 50
    average_duration = 2.5
    peak_hour = factory.LazyFunction(lambda: datetime.now().time())
    occupancy_rate = 75.5

class MonthlyReportFactory(DjangoModelFactory):
    class Meta:
        model = MonthlyReport

    year = factory.Sequence(lambda n: datetime.now().year - (n // 12))
    month = factory.Sequence(lambda n: (datetime.now().month - n) % 12 + 1)
    total_revenue = Decimal('30000.00')
    total_reservations = 1500
    average_duration = 2.5
    peak_day = factory.LazyFunction(lambda: datetime.now().date())
    average_occupancy_rate = 75.5

class ParkingLotReportFactory(DjangoModelFactory):
    class Meta:
        model = ParkingLotReport

    parking_lot = factory.SubFactory(ParkingLotUserOwnedFactory)
    date = factory.Sequence(lambda n: (datetime.now() - timedelta(days=n+1)).date())
    total_revenue = Decimal('5000.00')
    total_reservations = 250
    occupancy_rate = 85.0
    average_duration = 2.5
    peak_hour = factory.LazyFunction(lambda: datetime.now().time()) 