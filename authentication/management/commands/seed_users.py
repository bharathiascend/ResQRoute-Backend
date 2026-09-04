from django.core.management.base import BaseCommand
from authentication.models import User, UserRole, DriverProfile, CustomerProfile


class Command(BaseCommand):
    help = 'Seeds initial test accounts (Admin, Driver, Customer) for ResQRoute'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding ResQRoute users..."))

        # 1. Admin / Control Center user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@resqroute.gov.in',
                'first_name': 'Control',
                'last_name': 'Admin',
                'role': UserRole.ADMIN,
                'organization': 'MDoNER Logistics Authority',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created Admin: admin / admin123"))
        else:
            self.stdout.write("Admin account already exists.")

        # 2. Driver user (Matching SIH26002 seed: TR-102, DRV-001)
        driver_user, created = User.objects.get_or_create(
            username='driver1',
            defaults={
                'email': 'driver1@resqroute.gov.in',
                'first_name': 'Assigned',
                'last_name': 'Driver',
                'role': UserRole.DRIVER,
                'phone_number': '+91 98765 43210',
                'organization': 'Assam State Transport Corporation',
            }
        )
        if created:
            driver_user.set_password('driver123')
            driver_user.save()
            DriverProfile.objects.create(
                user=driver_user,
                vehicle_number='TR-102',
                license_number='DRV-001',
                is_available=True,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS("[OK] Created Driver: driver1 / driver123 (TR-102, DRV-001)"))
        else:
            self.stdout.write("Driver account already exists.")

        # 3. Customer / Operations user
        customer_user, created = User.objects.get_or_create(
            username='customer1',
            defaults={
                'email': 'customer1@resqroute.gov.in',
                'first_name': 'Operations',
                'last_name': 'Requester',
                'role': UserRole.CUSTOMER,
                'phone_number': '+91 91234 56789',
                'organization': 'Guwahati Medical College & Hospital',
            }
        )
        if created:
            customer_user.set_password('customer123')
            customer_user.save()
            CustomerProfile.objects.create(
                user=customer_user,
                department='Emergency Medical Supplies',
                delivery_address='Silchar Civil Hospital, Assam'
            )
            self.stdout.write(self.style.SUCCESS("[OK] Created Customer: customer1 / customer123 (Guwahati Medical)"))
        else:
            self.stdout.write("Customer account already exists.")

        self.stdout.write(self.style.SUCCESS("\nAll ResQRoute seed users successfully created!"))
