from django.test import TestCase
from app.api.parking_lots.models import ParkingLot, ParkingSpace
from app.test.factories import (
    AdminUserFactory,
    ParkingLotUserOwnedFactory,
    ParkingSpaceFactory
)
from decimal import Decimal

class ParkingLotModelTests(TestCase):
    def setUp(self):
        self.owner = AdminUserFactory()
        self.parking_lot = ParkingLotUserOwnedFactory(owner=self.owner)

    def test_parking_lot_creation(self):
        """Test parking lot creation"""
        self.assertTrue(self.parking_lot.name.startswith('Parking Lot'))
        self.assertEqual(self.parking_lot.total_spaces, 50)
        self.assertEqual(self.parking_lot.available_spaces, 50)
        self.assertEqual(self.parking_lot.hourly_rate, Decimal('10.00'))
        self.assertEqual(self.parking_lot.owner, self.owner)
        self.assertEqual(self.parking_lot.status, ParkingLot.Status.ACTIVE)
        self.assertIsNotNone(self.parking_lot.created_at)
        self.assertIsNotNone(self.parking_lot.updated_at)

    def test_parking_lot_str(self):
        """Test parking lot string representation"""
        self.assertTrue(str(self.parking_lot).startswith('Parking Lot'))

    def test_parking_lot_update(self):
        """Test parking lot update"""
        self.parking_lot.name = 'Updated Parking Lot'
        self.parking_lot.hourly_rate = Decimal('15.00')
        self.parking_lot.status = ParkingLot.Status.MAINTENANCE
        self.parking_lot.save()
        
        updated_lot = ParkingLot.objects.get(id=self.parking_lot.id)
        self.assertEqual(updated_lot.name, 'Updated Parking Lot')
        self.assertEqual(updated_lot.hourly_rate, Decimal('15.00'))
        self.assertEqual(updated_lot.status, ParkingLot.Status.MAINTENANCE)

    def test_parking_lot_delete(self):
        """Test parking lot deletion"""
        lot_id = self.parking_lot.id
        self.parking_lot.delete()
        self.assertFalse(ParkingLot.objects.filter(id=lot_id).exists())

    def test_parking_lot_occupancy_rate(self):
        """Test parking lot occupancy rate calculation"""
        self.assertEqual(self.parking_lot.occupancy_rate, 0)  # All spaces available
        
        self.parking_lot.available_spaces = 25
        self.parking_lot.save()
        self.assertEqual(self.parking_lot.occupancy_rate, 50)  # Half occupied
        
        self.parking_lot.available_spaces = 0
        self.parking_lot.save()
        self.assertEqual(self.parking_lot.occupancy_rate, 100)  # Fully occupied

class ParkingSpaceModelTests(TestCase):
    def setUp(self):
        self.owner = AdminUserFactory()
        self.parking_lot = ParkingLotUserOwnedFactory(owner=self.owner)
        self.parking_space = ParkingSpaceFactory(parking_lot=self.parking_lot)

    def test_parking_space_creation(self):
        """Test parking space creation"""
        self.assertEqual(self.parking_space.parking_lot, self.parking_lot)
        self.assertTrue(self.parking_space.space_number.startswith('A'))
        self.assertEqual(self.parking_space.status, ParkingSpace.Status.AVAILABLE)
        self.assertIsNone(self.parking_space.current_user)
        self.assertIsNotNone(self.parking_space.created_at)
        self.assertIsNotNone(self.parking_space.updated_at)

    def test_parking_space_str(self):
        """Test parking space string representation"""
        self.assertTrue(str(self.parking_space).startswith(self.parking_lot.name))
        self.assertTrue('Space' in str(self.parking_space))

    def test_parking_space_update(self):
        """Test parking space update"""
        self.parking_space.status = ParkingSpace.Status.OCCUPIED
        self.parking_space.current_user = self.owner
        self.parking_space.save()
        
        updated_space = ParkingSpace.objects.get(id=self.parking_space.id)
        self.assertEqual(updated_space.status, ParkingSpace.Status.OCCUPIED)
        self.assertEqual(updated_space.current_user, self.owner)

    def test_parking_space_delete(self):
        """Test parking space deletion"""
        space_id = self.parking_space.id
        self.parking_space.delete()
        self.assertFalse(ParkingSpace.objects.filter(id=space_id).exists())

    def test_parking_space_validation(self):
        """Test parking space validation"""
        # Test duplicate space number
        with self.assertRaises(Exception):
            ParkingSpace.objects.create(
                parking_lot=self.parking_lot,
                space_number=self.parking_space.space_number,
                status=ParkingSpace.Status.AVAILABLE
            )

        # Test invalid status
        with self.assertRaises(Exception):
            ParkingSpace.objects.create(
                parking_lot=self.parking_lot,
                space_number='A2',
                status='invalid_status'
            ) 