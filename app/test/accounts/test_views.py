from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from app.api.accounts.models import Profile
from app.test.factories import UserFactory, AdminUserFactory
from django.contrib.auth import get_user_model

User = get_user_model()

class UserViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = AdminUserFactory()
        self.regular_user = UserFactory()
        self.client.force_authenticate(user=self.admin_user)

    def test_list_users(self):
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin can see all users
        self.assertEqual(len(response.data['results']), User.objects.count())

    def test_create_user(self):
        url = reverse('user-list')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'user',
            'status': 'active'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        # Profile is automatically created
        self.assertEqual(Profile.objects.count(), 3)

    def test_update_user(self):
        url = reverse('user-detail', args=[self.regular_user.id])
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')
        self.assertEqual(self.regular_user.last_name, 'Name')

    def test_delete_user(self):
        url = reverse('user-detail', args=[self.regular_user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 1)

    def test_regular_user_cannot_list_users(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('user-list')
        response = self.client.get(url)
        # Regular users can only see their own profile
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class ProfileViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = AdminUserFactory()
        self.regular_user = UserFactory()
        self.client.force_authenticate(user=self.admin_user)

    def test_list_profiles(self):
        url = reverse('profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_profile(self):
        url = reverse('profile-list')
        data = {
            'phone_number': '+1234567890',
            'address': '123 Test St'
        }
        # Get the existing profile
        profile = Profile.objects.get(user=self.admin_user)
        url = reverse('profile-detail', args=[profile.id])
        # Update the profile instead of creating a new one
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify the profile was updated with correct data
        profile.refresh_from_db()
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.address, '123 Test St')

    def test_update_profile(self):
        profile = Profile.objects.get(user=self.regular_user)
        url = reverse('profile-detail', args=[profile.id])
        data = {
            'phone_number': '+0987654321',
            'address': '456 New St'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.phone_number, '+0987654321')
        self.assertEqual(profile.address, '456 New St')

    def test_regular_user_can_view_own_profile(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_regular_user_cannot_view_other_profiles(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) 