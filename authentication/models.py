from django.db import models
from django.contrib.auth.models import AbstractUser


class UserRole(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Customer'
    DRIVER = 'DRIVER', 'Field Driver'
    ADMIN = 'ADMIN', 'Government Official / Authority'


class AreaType(models.TextChoices):
    CITY = 'CITY', 'City / Urban'
    VILLAGE = 'VILLAGE', 'Village / Rural'


class ApprovalStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Superadmin Approval'
    APPROVED = 'APPROVED', 'Approved / Verified Authority'
    REJECTED = 'REJECTED', 'Rejected'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        help_text="Role-based access level for ResQRoute"
    )
    phone_number = models.CharField(max_length=20, blank=True)
    organization = models.CharField(max_length=150, blank=True)

    def is_driver(self):
        return self.role == UserRole.DRIVER

    def is_customer(self):
        return self.role == UserRole.CUSTOMER

    def is_authority(self):
        return self.role == UserRole.ADMIN

    def is_admin_user(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class DriverProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )
    vehicle_type = models.CharField(
        max_length=60,
        default='Heavy Emergency Truck',
        help_text="Truck or cargo vehicle specification"
    )
    vehicle_number = models.CharField(
        max_length=50,
        help_text="Assigned or primary vehicle identifier (e.g. TR-102)"
    )
    license_number = models.CharField(
        max_length=50,
        help_text="Official driving license or driver ID (e.g. TN01 20190001234)"
    )
    license_issuing_state = models.CharField(
        max_length=50,
        blank=True,
        help_text="State where driving license was issued"
    )
    license_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="License expiry date"
    )
    state = models.CharField(
        max_length=50,
        blank=True,
        help_text="Operating or registered state"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        help_text="Operating or registered district"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Availability status for dispatch and trip activation"
    )
    is_verified = models.BooleanField(
        default=True,
        help_text="Verification status by logistics authority"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Driver: {self.user.get_full_name() or self.user.username} ({self.vehicle_type} - {self.vehicle_number})"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    area_type = models.CharField(
        max_length=20,
        choices=AreaType.choices,
        default=AreaType.CITY,
        help_text="Urban city vs rural village locality"
    )
    locality_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="City or Village name"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        help_text="District location"
    )
    pincode = models.CharField(
        max_length=10,
        blank=True,
        help_text="6-digit postal code"
    )
    state = models.CharField(
        max_length=50,
        blank=True,
        help_text="North Eastern state jurisdiction"
    )
    department = models.CharField(max_length=100, blank=True)
    delivery_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        loc = self.locality_name or self.state or 'General'
        return f"Customer: {self.user.get_full_name() or self.user.username} ({loc})"


class AuthorityProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='authority_profile'
    )
    official_id = models.CharField(
        max_length=60,
        help_text="Official Government Employee ID or Service Badge Code (e.g. MDoNER-AS-102)"
    )
    designation = models.CharField(
        max_length=150,
        help_text="Official government rank or title (e.g. District Disaster Management Officer)"
    )
    department_name = models.CharField(
        max_length=150,
        help_text="Government agency or ministry (e.g. MDoNER, ASDMA, BRO, NDRF)"
    )
    jurisdiction_state = models.CharField(
        max_length=50,
        help_text="State or regional jurisdiction across North Eastern corridor"
    )
    district_office = models.CharField(
        max_length=100,
        blank=True,
        help_text="District office or regional jurisdiction (Optional)"
    )
    office_address = models.TextField(
        blank=True,
        help_text="Official government office or district headquarters address"
    )
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        help_text="Verification status by central developer/superadmin"
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_authorities',
        help_text="Superadmin who verified this authority"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Authority: {self.user.get_full_name() or self.user.username} ({self.designation} - {self.jurisdiction_state} [{self.approval_status}])"


class OfficialPasswordResetRequest(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_requests'
    )
    official_id = models.CharField(max_length=60)
    email = models.EmailField(blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )
    temp_password = models.CharField(max_length=128, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_password_resets'
    )

    def __str__(self):
        return f"ResetRequest: {self.official_id} ({self.user.username}) [{self.status}]"
