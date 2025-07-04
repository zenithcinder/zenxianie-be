from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from app.api.parking_lots.models import ParkingLot, ParkingSpace
from app.test.factories import ParkingLotUserOwnedFactory, ParkingSpaceFactory, AdminUserFactory, UserFactory
from decimal import Decimal

class ParkingLotViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = AdminUserFactory()
        self.regular_user = UserFactory()
        self.client.force_authenticate(user=self.admin_user)
        self.parking_lot = ParkingLotUserOwnedFactory(owner=self.admin_user)
        self.parking_space = ParkingSpaceFactory(parking_lot=self.parking_lot)

    def test_list_parking_lots(self):
        url = reverse('parking-lot-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_parking_lot(self):
        url = reverse('parking-lot-list')
        data = {
            'name': 'New Parking Lot',
            'address': '123 Test St',
            'latitude': 14.5995,
            'longitude': 120.9842,
            'total_spaces': 100,
            'available_spaces': 100,  # Must match total_spaces initially
            'hourly_rate': '15.00',
            'status': ParkingLot.Status.ACTIVE
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ParkingLot.objects.count(), 2)
        # Verify the parking lot was created with correct data
        parking_lot = ParkingLot.objects.get(name='New Parking Lot')
        self.assertEqual(parking_lot.address, '123 Test St')
        self.assertEqual(parking_lot.total_spaces, 100)
        self.assertEqual(parking_lot.available_spaces, 100)
        self.assertEqual(parking_lot.hourly_rate, Decimal('15.00'))
        self.assertEqual(parking_lot.status, ParkingLot.Status.ACTIVE)

    def test_update_parking_lot(self):
        url = reverse('parking-lot-detail', args=[self.parking_lot.id])
        data = {
            'name': 'Updated Parking Lot',
            'hourly_rate': '20.00'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parking_lot.refresh_from_db()
        self.assertEqual(self.parking_lot.name, 'Updated Parking Lot')
        self.assertEqual(self.parking_lot.hourly_rate, 20.00)

    def test_delete_parking_lot(self):
        url = reverse('parking-lot-detail', args=[self.parking_lot.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ParkingLot.objects.count(), 0)

    def test_regular_user_cannot_create_parking_lot(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('parking-lot-list')
        data = {
            'name': 'New Parking Lot',
            'address': '123 Test St',
            'latitude': 14.5995,
            'longitude': 120.9842,
            'total_spaces': 100,
            'hourly_rate': '15.00'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_update_parking_lot(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('parking-lot-detail', args=[self.parking_lot.id])
        data = {'name': 'Updated Parking Lot'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class ParkingSpaceViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = AdminUserFactory()
        self.regular_user = UserFactory()
        self.client.force_authenticate(user=self.admin_user)
        self.parking_lot = ParkingLotUserOwnedFactory(owner=self.admin_user)
        self.parking_space = ParkingSpaceFactory(parking_lot=self.parking_lot)

    def test_list_parking_spaces(self):
        url = reverse('parking-space-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_parking_space(self):
        url = reverse('parking-space-list')
        data = {
            'parking_lot': self.parking_lot.id,
            'space_number': 'B1',
            'status': ParkingSpace.Status.AVAILABLE
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ParkingSpace.objects.count(), 2)

    def test_update_parking_space(self):
        url = reverse('parking-space-detail', args=[self.parking_space.id])
        data = {
            'status': ParkingSpace.Status.MAINTENANCE
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parking_space.refresh_from_db()
        self.assertEqual(self.parking_space.status, ParkingSpace.Status.MAINTENANCE)

    def test_delete_parking_space(self):
        url = reverse('parking-space-detail', args=[self.parking_space.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ParkingSpace.objects.count(), 0)

    def test_regular_user_cannot_create_parking_space(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('parking-space-list')
        data = {
            'parking_lot': self.parking_lot.id,
            'space_number': 'B1',
            'status': ParkingSpace.Status.AVAILABLE
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_update_parking_space(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('parking-space-detail', args=[self.parking_space.id])
        data = {'status': ParkingSpace.Status.MAINTENANCE}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 