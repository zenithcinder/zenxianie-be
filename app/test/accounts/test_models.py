from django.test import TestCase
from django.contrib.auth import get_user_model
from app.api.accounts.models import Profile
from app.api.accounts.serializers import UserProfileSerializer
from app.test.factories import UserFactory, AdminUserFactory

User = get_user_model()

class UserModelTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.admin_user = AdminUserFactory()

    def test_create_user(self):
        """Test user creation"""
        self.assertTrue(self.user.email.endswith('@example.com'))
        self.assertTrue(self.user.username.startswith('user'))
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.user.role, 'user')
        self.assertEqual(self.user.status, 'active')

    def test_create_superuser(self):
        """Test superuser creation"""
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)
        self.assertEqual(self.admin_user.role, 'admin')

    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), f'{self.user.first_name} {self.user.last_name} ({self.user.email})')

class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        # Profile is automatically created by the signal
        self.profile = Profile.objects.get(user=self.user)
        self.profile.phone_number = '+1234567890'
        self.profile.address = '123 Test St'
        self.profile.save()

    def test_profile_creation(self):
        """Test user profile creation"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.phone_number, '+1234567890')
        self.assertEqual(self.profile.address, '123 Test St')
        self.assertTrue(isinstance(self.profile, Profile))
        self.assertEqual(str(self.profile), self.user.email)

    def test_profile_serializer(self):
        """Test user profile serializer"""
        serializer = UserProfileSerializer(self.profile)
        self.assertEqual(serializer.data['phone_number'], '+1234567890')
        self.assertEqual(serializer.data['user']['email'], self.user.email)

    def test_profile_update(self):
        """Test user profile update"""
        self.profile.phone_number = '+0987654321'
        self.profile.address = '456 New St'
        self.profile.save()
        self.assertEqual(self.profile.phone_number, '+0987654321')
        self.assertEqual(self.profile.address, '456 New St')

    def test_profile_delete(self):
        """Test user profile deletion"""
        profile_id = self.profile.id
        self.profile.delete()
        self.assertFalse(Profile.objects.filter(id=profile_id).exists()) 