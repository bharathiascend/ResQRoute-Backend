import uuid
from django.db import models
from django.conf import settings


class CargoType(models.TextChoices):
    MEDICINE = 'MEDICINE', 'Critical Medicine & Vaccines'
    FOOD = 'FOOD', 'Emergency Rations & Potable Water'
    RELIEF = 'RELIEF', 'Disaster Relief Supplies & Tents'
    DISASTER_AID = 'DISASTER_AID', 'Rescue Gear & Power Generators'
    GENERAL = 'GENERAL', 'General Cargo'


class CargoPriority(models.TextChoices):
    CRITICAL = 'CRITICAL', 'Critical Priority (Life-Saving)'
    HIGH = 'HIGH', 'High Priority (Expedited Dispatch)'
    NORMAL = 'NORMAL', 'Standard Priority'


class ShipmentStatus(models.TextChoices):
    READY = 'READY', 'Ready for Dispatch'
    ASSIGNED = 'ASSIGNED', 'Assigned to Field Driver'
    IN_TRANSIT = 'IN_TRANSIT', 'In-Transit on Corridor'
    DELIVERED = 'DELIVERED', 'Delivered & Verified'
    CANCELLED = 'CANCELLED', 'Cancelled'


class RiskLevel(models.TextChoices):
    SAFE = 'SAFE', 'Safe Corridor (< 35)'
    CAUTION = 'CAUTION', 'Cautionary Alert (35 - 69)'
    BLOCKED = 'BLOCKED', 'High Risk / Blocked (≥ 70)'


class TripStatus(models.TextChoices):
    READY = 'READY', 'Pending QR Activation'
    ACTIVE = 'ACTIVE', 'Trip Active (Departed Base)'
    IN_TRANSIT = 'IN_TRANSIT', 'In-Transit on Mountain Pass'
    COMPLETED = 'COMPLETED', 'Trip Completed & Reached'


class Shipment(models.Model):
    shipment_code = models.CharField(
        max_length=40,
        unique=True,
        help_text="Unique corridor shipment identifier (e.g. RSQ-102)"
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shipments',
        help_text="User/Organization who requisitioned this shipment"
    )
    cargo_type = models.CharField(
        max_length=40,
        choices=CargoType.choices,
        default=CargoType.MEDICINE
    )
    cargo_priority = models.CharField(
        max_length=30,
        choices=CargoPriority.choices,
        default=CargoPriority.CRITICAL
    )
    origin = models.CharField(
        max_length=150,
        help_text="Dispatch origin location (e.g. Guwahati Central Medical Hub)"
    )
    destination = models.CharField(
        max_length=150,
        help_text="Delivery destination (e.g. Silchar Civil Hospital)"
    )
    weight_kg = models.FloatField(
        default=500.0,
        help_text="Total shipment cargo weight in kilograms"
    )
    delivery_address = models.TextField(
        blank=True,
        help_text="Specific street/district delivery address"
    )
    special_instructions = models.TextField(
        blank=True,
        help_text="Handling guidelines (e.g. Cold-chain refrigeration required)"
    )
    status = models.CharField(
        max_length=30,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.READY
    )
    is_emergency_relief = models.BooleanField(
        default=True,
        help_text="Priority corridor clearance for MDoNER / NDMA relief"
    )

    # AI Risk Engine outputs (Powered by OpenAI)
    risk_score = models.IntegerField(
        default=24,
        help_text="Corridor hazard composite score (0-100)"
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.SAFE
    )
    risk_summary = models.TextField(
        blank=True,
        help_text="AI explainability summary of route safety"
    )
    risk_factors = models.JSONField(
        default=list,
        blank=True,
        help_text="Bullet points explaining why route was scored this way"
    )
    recommended_route = models.CharField(
        max_length=255,
        blank=True,
        help_text="Primary corridor or alternate ridge reroute"
    )

    # QR Trip Activation Token
    qr_token = models.CharField(
        max_length=64,
        unique=True,
        help_text="Unique cryptographic token encoded into Driver QR badge"
    )
    qr_svg = models.TextField(
        blank=True,
        help_text="Inline SVG / Data URL for driver scanning"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment {self.shipment_code}: {self.cargo_type} ({self.origin} → {self.destination})"


class Trip(models.Model):
    trip_code = models.CharField(
        max_length=40,
        unique=True,
        help_text="Trip activation identifier (e.g. TRIP-102)"
    )
    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        related_name='trip'
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips',
        help_text="Field driver assigned to this trip"
    )
    vehicle_number = models.CharField(
        max_length=50,
        default='TR-102',
        help_text="Assigned vehicle plate"
    )
    vehicle_type = models.CharField(
        max_length=60,
        default='Heavy Emergency Truck (6-10W)',
        help_text="Vehicle capacity spec"
    )
    status = models.CharField(
        max_length=30,
        choices=TripStatus.choices,
        default=TripStatus.READY
    )
    current_corridor_segment = models.CharField(
        max_length=150,
        default='Guwahati Outskirts (NH-27 Junction)',
        help_text="Live physical road segment ID"
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when driver scanned and verified QR code"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    last_ping_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last telemetry or checkpoint check-in"
    )
    route_advisory = models.TextField(
        blank=True,
        default='Proceed with standard mountain driving precautions.',
        help_text="Driver-specific advisory based on AI terrain assessment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Trip {self.trip_code} for {self.shipment.shipment_code} [{self.status}]"
