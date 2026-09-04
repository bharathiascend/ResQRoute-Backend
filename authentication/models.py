from django.db import models
from django.contrib.auth.models import AbstractUser


class UserRole(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Customer / User'
    DRIVER = 'DRIVER', 'Driver'
    ADMIN = 'ADMIN', 'Admin / Control Center'


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
    vehicle_number = models.CharField(
        max_length=50,
        help_text="Assigned or primary vehicle identifier (e.g. TR-102)"
    )
    license_number = models.CharField(
        max_length=50,
        help_text="Official driving license or driver ID (e.g. DRV-001)"
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
        return f"Driver: {self.user.get_full_name() or self.user.username} (Vehicle: {self.vehicle_number})"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    department = models.CharField(max_length=100, blank=True)
    delivery_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Customer: {self.user.get_full_name() or self.user.username} ({self.user.organization or 'General'})"
