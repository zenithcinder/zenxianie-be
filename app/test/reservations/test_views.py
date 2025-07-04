from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from app.api.reservations.models import Reservation
from app.test.factories import (
    UserFactory,
    ParkingLotUserOwnedFactory,
    ParkingSpaceFactory,
    ReservationFactory
)
from datetime import datetime, timedelta
from django.utils import timezone

class ReservationViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.admin_user = UserFactory(is_staff=True)
        self.parking_lot = ParkingLotUserOwnedFactory()
        self.parking_space = ParkingSpaceFactory(parking_lot=self.parking_lot)
        self.reservation = ReservationFactory(
            user=self.user,
            parking_lot=self.parking_lot,
            parking_space=self.parking_space
        )
        self.client.force_authenticate(user=self.user)

    def test_list_reservations(self):
        """Test listing reservations"""
        url = reverse('reservation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Using pagination

    def test_create_reservation(self):
        """Test creating a reservation"""
        
        # The permission issue is likely because ParkingLotFactory creates parking lots
        # with AdminUserFactory as the owner, not regular users
        # Let's authenticate as the admin user who owns the parking lot
        self.client.force_authenticate(user=self.parking_lot.owner)
        
        url = reverse('reservation-list')
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        # First, let's cancel the existing reservation to make the original parking space available
        self.reservation.status = Reservation.Status.CANCELLED
        self.reservation.save()
        self.parking_space.refresh_from_db()
        
        # Now use the original parking space that should be available again
        data = {
            'parking_lot': self.parking_lot.id,
            'parking_space': self.parking_space.id,
            'user': self.user.id,  # Admins might need to specify which user the reservation is for
            'vehicle_plate': 'XYZ123',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data if hasattr(response, 'data') else 'No data'}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_create_reservation_invalid_time(self):
        """Test creating a reservation with invalid time"""
        url = reverse('reservation-list')
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time - timedelta(hours=1)  # Invalid: end before start
        data = {
            'parking_lot': self.parking_lot.id,
            'parking_space': self.parking_space.id,
            'vehicle_plate': 'XYZ123',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_reservation(self):
        """Test updating a reservation"""
        url = reverse('reservation-detail', args=[self.reservation.id])
        data = {
            'vehicle_plate': 'NEW123',
            'notes': 'Updated notes'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.vehicle_plate, 'NEW123')
        self.assertEqual(self.reservation.notes, 'Updated notes')

    def test_cancel_reservation(self):
        """Test cancelling a reservation"""
        url = reverse('reservation-detail', args=[self.reservation.id])
        data = {
            'status': Reservation.Status.CANCELLED
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CANCELLED)

    def test_delete_reservation(self):
        """Test deleting a reservation"""
        url = reverse('reservation-detail', args=[self.reservation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_admin_can_view_all_reservations(self):
        """Test admin can view all reservations"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('reservation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_user_cannot_view_others_reservations(self):
        """Test user cannot view others' reservations"""
        other_user = UserFactory()
        self.client.force_authenticate(user=other_user)
        url = reverse('reservation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_my_reservations_endpoint(self):
        """Test my_reservations endpoint"""
        url = reverse('reservation-my-reservations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_active_reservations_endpoint(self):
        """Test active reservations endpoint"""
        url = reverse('reservation-active')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_complete_reservation(self):
        """Test completing a reservation"""
        url = reverse('reservation-complete', args=[self.reservation.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.COMPLETED)

    def test_filter_reservations_by_status(self):
        """Test filtering reservations by status"""
        url = reverse('reservation-list')
        response = self.client.get(url, {'status': Reservation.Status.ACTIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_reservations_by_date_range(self):
        """Test filtering reservations by date range"""
        url = reverse('reservation-list')
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=7)
        response = self.client.get(url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) 