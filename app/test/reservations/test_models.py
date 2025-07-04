from django.test import TestCase
from django.contrib.auth import get_user_model
from app.api.parking_lots.models import ParkingLot, ParkingSpace
from app.api.reservations.models import Reservation
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from app.test.factories import (
    UserFactory,
    ParkingLotUserOwnedFactory,
    ParkingSpaceFactory,
    ReservationFactory
)

User = get_user_model()

class ReservationModelTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.parking_lot = ParkingLotUserOwnedFactory()
        self.parking_space = ParkingSpaceFactory(parking_lot=self.parking_lot)
        self.start_time = timezone.now() + timedelta(hours=1)
        self.end_time = self.start_time + timedelta(hours=2)
        self.reservation = ReservationFactory(
            user=self.user,
            parking_lot=self.parking_lot,
            parking_space=self.parking_space,
            start_time=self.start_time,
            end_time=self.end_time
        )

    def test_reservation_creation(self):
        """Test reservation creation"""
        self.assertEqual(self.reservation.user, self.user)
        self.assertEqual(self.reservation.parking_lot, self.parking_lot)
        self.assertEqual(self.reservation.parking_space, self.parking_space)
        self.assertEqual(self.reservation.start_time, self.start_time)
        self.assertEqual(self.reservation.end_time, self.end_time)
        self.assertEqual(self.reservation.status, Reservation.Status.ACTIVE)
        self.assertIsNotNone(self.reservation.vehicle_plate)
        self.assertIsNotNone(self.reservation.created_at)
        self.assertIsNotNone(self.reservation.updated_at)

    def test_reservation_str(self):
        """Test reservation string representation"""
        expected_str = f"Reservation {self.reservation.id} - {self.user.get_full_name()}"
        self.assertEqual(str(self.reservation), expected_str)

    def test_reservation_duration(self):
        """Test reservation duration calculation"""
        self.assertEqual(self.reservation.duration, Decimal('2.0'))

    def test_reservation_total_cost(self):
        """Test reservation total cost calculation"""
        expected_cost = self.parking_lot.hourly_rate * Decimal('2.0')
        self.assertEqual(self.reservation.total_cost, expected_cost)

    def test_reservation_status_transitions(self):
        """Test reservation status transitions"""
        # Test active to completed
        self.reservation.status = Reservation.Status.COMPLETED
        self.reservation.save()
        self.assertEqual(self.reservation.status, Reservation.Status.COMPLETED)

        # Test active to cancelled
        self.reservation.status = Reservation.Status.CANCELLED
        self.reservation.save()
        self.assertEqual(self.reservation.status, Reservation.Status.CANCELLED)

    def test_reservation_validation(self):
        """Test reservation validation"""
        # Test end time before start time
        with self.assertRaises(Exception):
            Reservation.objects.create(
                user=self.user,
                parking_lot=self.parking_lot,
                parking_space=self.parking_space,
                start_time=self.end_time,
                end_time=self.start_time,
                vehicle_plate='XYZ789'
            )

        # Test overlapping reservation
        with self.assertRaises(Exception):
            Reservation.objects.create(
                user=self.user,
                parking_lot=self.parking_lot,
                parking_space=self.parking_space,
                start_time=self.start_time + timedelta(hours=1),
                end_time=self.end_time + timedelta(hours=1),
                vehicle_plate='XYZ789'
            )

    def test_reservation_delete(self):
        """Test reservation deletion"""
        reservation_id = self.reservation.id
        self.reservation.delete()
        self.assertFalse(Reservation.objects.filter(id=reservation_id).exists())

    def test_parking_space_status_update(self):
        """Test parking space status updates with reservation"""
        # Test space becomes reserved on creation
        self.assertEqual(self.parking_space.status, ParkingSpace.Status.RESERVED)
        self.assertEqual(self.parking_space.current_user, self.user)

        # Test space becomes available on cancellation
        self.reservation.status = Reservation.Status.CANCELLED
        self.reservation.save()
        self.parking_space.refresh_from_db()
        self.assertEqual(self.parking_space.status, ParkingSpace.Status.AVAILABLE)
        self.assertIsNone(self.parking_space.current_user)

    def test_parking_lot_spaces_update(self):
        """Test parking lot available spaces updates"""
        # Since we created a reservation in setUp, available spaces should be total spaces - 1
        total_spaces = self.parking_lot.total_spaces
        self.assertEqual(self.parking_lot.available_spaces, total_spaces - 1)
        
        # Store current available spaces before cancellation
        current_spaces = self.parking_lot.available_spaces
        
        # Test spaces increase on cancellation
        self.reservation.status = Reservation.Status.CANCELLED
        self.reservation.save()
        self.parking_lot.refresh_from_db()
        self.assertEqual(self.parking_lot.available_spaces, current_spaces + 1) 