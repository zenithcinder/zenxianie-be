from django.test import TestCase
from django.conf import settings
import os

class EnvironmentVariablesTest(TestCase):
    def setUp(self):
        print("\n=== Test Environment Variables ===")
        print(f"DJANGO_CORS_ALLOWED_ORIGINS from env: {os.getenv('DJANGO_CORS_ALLOWED_ORIGINS')}")
        print(f"CORS_ALLOWED_ORIGINS from settings: {settings.CORS_ALLOWED_ORIGINS}")
        print("================================\n")

    def test_env_variables_loaded(self):
        """Test that environment variables are properly loaded"""
        # Test Django settings
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertIsNotNone(settings.DEBUG)
        self.assertIsNotNone(settings.ALLOWED_HOSTS)
        
        # Test Database settings
        # During tests, Django creates a test database with a different name
        if 'test' in settings.DATABASES['default']['NAME']:
            self.assertTrue(settings.DATABASES['default']['NAME'].startswith('test_'))
        else:
            self.assertEqual(settings.DATABASES['default']['NAME'], 'zenxianie_parking')
        
        self.assertEqual(settings.DATABASES['default']['USER'], 'postgres')
        self.assertEqual(settings.DATABASES['default']['PASSWORD'], 'postgres')
        self.assertEqual(settings.DATABASES['default']['PORT'], '5435')
        
        # Test CORS settings
        self.assertIn('http://localhost:5173', settings.CORS_ALLOWED_ORIGINS)
        self.assertIn('http://127.0.0.1:5173', settings.CORS_ALLOWED_ORIGINS) 