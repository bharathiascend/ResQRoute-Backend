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
            'area_type': 'CITY',
            'locality_name': 'Guwahati Hub',
            'pincode': '781001',
            'state': 'Assam',
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
        self.assertEqual(user.customer_profile.state, 'Assam')

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
            'vehicle_number': 'TR-102',
            'vehicle_type': 'HEAVY_TRUCK',
            'license_number': 'DRV-001',
            'license_issuing_state': 'Assam'
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
            'phone_number': '+91 9876543212',
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
        CustomerProfile.objects.create(user=user, locality_name='Guwahati', pincode='781001', state='Assam')

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

    def test_registration_sanitizes_username_with_spaces(self):
        """Verify username with spaces (e.g. 'Bharathi 02') is automatically sanitized to 'bharathi_02'."""
        payload = {
            'username': 'Bharathi 02',
            'email': 'bharathiascend@gmail.com',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'first_name': 'Bharathi',
            'role': UserRole.CUSTOMER,
            'phone_number': '782484954',
            'locality_name': 'Guwahati',
            'pincode': '781001',
            'state': 'Assam'
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'bharathi_02')
        self.assertTrue(User.objects.filter(username='bharathi_02').exists())

    def test_registration_duplicate_email_fails(self):
        """Verify duplicate email returns clean 400 error."""
        User.objects.create_user(
            username='user1',
            email='duplicate@example.com',
            password='Password123'
        )
        payload = {
            'username': 'user2',
            'email': 'duplicate@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': UserRole.CUSTOMER
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_authority_registration_requires_superadmin_approval(self):
        """Verify government official registers with PENDING status and cannot log in until approved."""
        payload = {
            'username': 'official_sikkim',
            'email': 'sikkim_official@gov.in',
            'password': 'OfficialPass123',
            'confirm_password': 'OfficialPass123',
            'first_name': 'Karma',
            'last_name': 'Bhutia',
            'role': UserRole.ADMIN,
            'official_id': 'SK-SDMA-099',
            'designation': 'Executive Disaster Officer',
            'department_name': 'Sikkim SDMA',
            'jurisdiction_state': 'Sikkim',
            'office_address': 'Tashiling Secretariat, Gangtok'
        }
        reg_response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reg_response.data['user']['role'], UserRole.ADMIN)

        # Official cannot log in while PENDING
        login_response = self.client.post('/api/auth/login/', {
            'username': 'official_sikkim',
            'password': 'OfficialPass123'
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('pending', str(login_response.data).lower())

        # Superadmin approves the official
        user = User.objects.get(username='official_sikkim')
        user.authority_profile.approval_status = 'APPROVED'
        user.authority_profile.save()

        # Official can now log in
        login_after = self.client.post('/api/auth/login/', {
            'username': 'official_sikkim',
            'password': 'OfficialPass123'
        }, format='json')
        self.assertEqual(login_after.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_after.data)

    def test_driver_registration_without_email_succeeds(self):
        """Verify field drivers in mountain terrain without email can register successfully."""
        payload = {
            'username': 'hilldriver99',
            'password': 'DriverPass123',
            'confirm_password': 'DriverPass123',
            'first_name': 'Tenzing',
            'role': UserRole.DRIVER,
            'phone_number': '+91 9436123456',
            'vehicle_number': 'SK-01-E-9999',
            'vehicle_type': 'HEAVY_TRUCK',
            'license_number': 'SK20230009999',
            'license_issuing_state': 'Sikkim'
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'hilldriver99')
        user = User.objects.get(username='hilldriver99')
        self.assertEqual(user.driver_profile.license_issuing_state, 'Sikkim')

    def test_reroute_reports_endpoint(self):
        """Verify reroute reports endpoint returns state data for Sikkim and Assam with corridor logs."""
        response = self.client.get('/api/auth/reroute-reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        states = [s['state'] for s in response.data['state_wise_reports']]
        self.assertIn('Sikkim', states)
        self.assertIn('Assam', states)
        sikkim_report = next(s for s in response.data['state_wise_reports'] if s['state'] == 'Sikkim')
        self.assertEqual(sikkim_report['reroute_count'], 42)
        self.assertTrue(len(response.data['corridor_logs']) > 0)

    def test_driver_forgot_password_sms_generates_temp_password(self):
        """Verify driver entering mobile number gets auto-generated temporary password."""
        user = User.objects.create_user(
            username='smsdriver',
            password='OldPassword123',
            role=UserRole.DRIVER,
            phone_number='+91 9876543210'
        )
        DriverProfile.objects.create(user=user, vehicle_number='TR-102', license_number='LIC-102')

        response = self.client.post('/api/auth/forgot-password/', {
            'role': UserRole.DRIVER,
            'phone_number': '9876543210'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['channel'], 'SMS')
        temp_pwd = response.data['temp_password']
        self.assertTrue(temp_pwd.startswith('Drv#'))

        # Verify driver can log in with new temp password
        login_res = self.client.post('/api/auth/login/', {
            'username': 'smsdriver',
            'password': temp_pwd
        }, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)

    def test_customer_forgot_password_email_generates_temp_password(self):
        """Verify customer entering email gets auto-generated temporary password."""
        user = User.objects.create_user(
            username='emailcust',
            email='cust_reset@example.com',
            password='OldPassword123',
            role=UserRole.CUSTOMER
        )
        CustomerProfile.objects.create(user=user, locality_name='Guwahati', pincode='781001', state='Assam')

        response = self.client.post('/api/auth/forgot-password/', {
            'role': UserRole.CUSTOMER,
            'email': 'cust_reset@example.com'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['channel'], 'EMAIL')
        temp_pwd = response.data['temp_password']
        self.assertTrue(temp_pwd.startswith('Cust#'))

        # Verify customer can log in with new temp password
        login_res = self.client.post('/api/auth/login/', {
            'username': 'emailcust',
            'password': temp_pwd
        }, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)

    def test_change_password_inside_dashboard(self):
        """Verify logged-in user can change their password inside dashboard."""
        user = User.objects.create_user(
            username='changepassuser',
            password='TempPassword123',
            role=UserRole.CUSTOMER
        )
        CustomerProfile.objects.create(user=user, locality_name='Guwahati', pincode='781001', state='Assam')

        # Login to get token
        login_res = self.client.post('/api/auth/login/', {
            'username': 'changepassuser',
            'password': 'TempPassword123'
        }, format='json')
        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Change password
        change_res = self.client.post('/api/auth/change-password/', {
            'current_password': 'TempPassword123',
            'new_password': 'MyNewPermanentPass123',
            'confirm_new_password': 'MyNewPermanentPass123'
        }, format='json')
        self.assertEqual(change_res.status_code, status.HTTP_200_OK)

        # Verify login works with new password
        self.client.credentials()
        login_new = self.client.post('/api/auth/login/', {
            'username': 'changepassuser',
            'password': 'MyNewPermanentPass123'
        }, format='json')
        self.assertEqual(login_new.status_code, status.HTTP_200_OK)


