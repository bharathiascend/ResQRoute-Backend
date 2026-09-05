from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Shipment, Trip, CargoType, CargoPriority, ShipmentStatus, RiskLevel, TripStatus

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'full_name']

    def get_full_name(self, obj):
        first = getattr(obj, 'first_name', '')
        last = getattr(obj, 'last_name', '')
        name = f"{first} {last}".strip()
        return name if name else obj.username


class TripBriefSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id', 'trip_code', 'vehicle_number', 'vehicle_type',
            'status', 'current_corridor_segment', 'activated_at',
            'completed_at', 'last_ping_at', 'route_advisory', 'driver_name'
        ]

    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.get_full_name() or obj.driver.username
        return 'Unassigned'


class ShipmentSerializer(serializers.ModelSerializer):
    customer = UserBriefSerializer(read_only=True)
    trip = TripBriefSerializer(read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id',
            'shipment_code',
            'customer',
            'cargo_type',
            'cargo_priority',
            'origin',
            'destination',
            'weight_kg',
            'delivery_address',
            'special_instructions',
            'status',
            'is_emergency_relief',
            'risk_score',
            'risk_level',
            'risk_summary',
            'risk_factors',
            'recommended_route',
            'qr_token',
            'qr_svg',
            'trip',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'shipment_code', 'customer', 'status',
            'risk_score', 'risk_level', 'risk_summary', 'risk_factors',
            'recommended_route', 'qr_token', 'qr_svg', 'trip',
            'created_at', 'updated_at'
        ]


class ShipmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            'cargo_type',
            'cargo_priority',
            'origin',
            'destination',
            'weight_kg',
            'delivery_address',
            'special_instructions',
            'is_emergency_relief',
        ]

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0 kg.")
        return value


class TripSerializer(serializers.ModelSerializer):
    shipment = ShipmentSerializer(read_only=True)
    driver = UserBriefSerializer(read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id',
            'trip_code',
            'shipment',
            'driver',
            'vehicle_number',
            'vehicle_type',
            'status',
            'current_corridor_segment',
            'activated_at',
            'completed_at',
            'last_ping_at',
            'route_advisory',
            'created_at',
            'updated_at',
        ]


class TripActivateSerializer(serializers.Serializer):
    qr_token = serializers.CharField(
        required=True,
        help_text="Cryptographic QR token or shipment code (e.g. RSQ-102)"
    )
    vehicle_number = serializers.CharField(
        required=False,
        default='TR-102',
        help_text="Vehicle plate assigned by field driver"
    )


class TripStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=TripStatus.choices,
        help_text="New trip status (ACTIVE, IN_TRANSIT, COMPLETED)"
    )
    current_corridor_segment = serializers.CharField(
        required=False,
        help_text="Optional updated checkpoint segment"
    )


class RouteRiskEvaluateSerializer(serializers.Serializer):
    origin = serializers.CharField(required=True)
    destination = serializers.CharField(required=True)
    cargo_type = serializers.CharField(required=False, default='MEDICINE')
    cargo_priority = serializers.CharField(required=False, default='CRITICAL')
    weight_kg = serializers.FloatField(required=False, default=500.0)
