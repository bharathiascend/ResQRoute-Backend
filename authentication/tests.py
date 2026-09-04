from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from authentication.models import User, UserRole, DriverProfile, CustomerProfile


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        """Verify health check endpoint returns 200 ok and correct payload."""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['service'], 'resqroute-api')

    def test_customer_registration(self):
        """Verify customer registration creates User and CustomerProfile."""
        payload = {
            'username': 'testcustomer',
            'email': 'customer@example.com',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'first_name': 'Test',
            'last_name': 'Customer',
            'role': UserRole.CUSTOMER,
            'phone_number': '+91 9876543210',
            'organization': 'Assam Relief Center',
            'department': 'Disaster Management',
            'delivery_address': 'Guwahati Hub'
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], UserRole.CUSTOMER)

        user = User.objects.get(username='testcustomer')
        self.assertEqual(user.role, UserRole.CUSTOMER)
        self.assertTrue(CustomerProfile.objects.filter(user=user).exists())
        self.assertEqual(user.customer_profile.department, 'Disaster Management')

    def test_driver_registration(self):
        """Verify driver registration creates User and DriverProfile with vehicle info."""
        payload = {
            'username': 'testdriver',
            'email': 'driver@example.com',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'first_name': 'Test',
            'last_name': 'Driver',
            'role': UserRole.DRIVER,
            'phone_number': '+91 9876543211',
            'organization': 'NER Logistics Corp',
            'vehicle_number': 'TR-102',
            'license_number': 'DRV-001'
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['role'], UserRole.DRIVER)

        user = User.objects.get(username='testdriver')
        self.assertEqual(user.role, UserRole.DRIVER)
        self.assertTrue(DriverProfile.objects.filter(user=user).exists())
        self.assertEqual(user.driver_profile.vehicle_number, 'TR-102')

    def test_driver_registration_missing_vehicle_fails(self):
        """Driver registration must fail if vehicle_number or license_number is missing."""
        payload = {
            'username': 'incompletedriver',
            'email': 'driver2@example.com',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': UserRole.DRIVER,
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('vehicle_number', response.data)

    def test_login_and_me_endpoint(self):
        """Verify login yields JWT and accessing /api/auth/me/ with bearer token succeeds."""
        user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='MyPassword123',
            role=UserRole.CUSTOMER
        )
        CustomerProfile.objects.create(user=user, department='Logistics')

        # 1. Login with username
        login_response = self.client.post('/api/auth/login/', {
            'username': 'existinguser',
            'password': 'MyPassword123'
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        token = login_response.data['access']

        # 2. Query /api/auth/me/ without token -> 401
        unauthed_response = self.client.get('/api/auth/me/')
        self.assertEqual(unauthed_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 3. Query /api/auth/me/ with Bearer token -> 200
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'existinguser')
        self.assertEqual(me_response.data['role'], UserRole.CUSTOMER)
