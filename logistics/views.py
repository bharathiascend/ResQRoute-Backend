import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import views, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

from .models import Shipment, Trip, ShipmentStatus, TripStatus, RiskLevel
from .serializers import (
    ShipmentSerializer,
    ShipmentCreateSerializer,
    TripSerializer,
    TripActivateSerializer,
    TripStatusUpdateSerializer,
    RouteRiskEvaluateSerializer,
)
from .ai_risk_engine import evaluate_corridor_risk
from .qr_service import generate_qr_svg, generate_qr_data_url

User = get_user_model()


class OptionalJWTAuthentication(JWTAuthentication):
    """
    Tolerates invalid/expired tokens without throwing 401 on public or demo endpoints.
    If token is valid, request.user is set; otherwise defaults to AnonymousUser.
    """
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, AuthenticationFailed):
            return None


def _get_next_shipment_code() -> str:
    count = Shipment.objects.count() + 101
    code = f"RSQ-{count}"
    while Shipment.objects.filter(shipment_code=code).exists():
        count += 1
        code = f"RSQ-{count}"
    return code


def _get_fallback_user():
    """Fallback user for unauthenticated / demo shipment requisition."""
    user = User.objects.filter(role='CUSTOMER').first()
    if not user:
        user = User.objects.first()
    return user


class ShipmentListCreateView(views.APIView):
    """
    GET: List all shipments or customer-specific shipments.
    POST: Requisition a new shipment, run AI risk evaluation, and generate QR badge.
    """
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        shipments = Shipment.objects.all().select_related('customer', 'trip').order_by('-created_at')
        if request.user.is_authenticated and request.user.role == 'CUSTOMER' and not request.query_params.get('all'):
            shipments = shipments.filter(customer=request.user)
        
        serializer = ShipmentSerializer(shipments, many=True)
        return Response({
            'count': shipments.count(),
            'shipments': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ShipmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        
        # 1. Determine Customer
        customer = request.user if request.user.is_authenticated else _get_fallback_user()

        # 2. Generate unique shipment code & QR token
        shipment_code = _get_next_shipment_code()
        qr_token = f"{shipment_code}-{uuid.uuid4().hex[:8].upper()}"

        # 3. Run AI Logic Risk Engine (powered by OpenAI gpt-4o-mini + North East corridor heuristics)
        risk_result = evaluate_corridor_risk(
            origin=data['origin'],
            destination=data['destination'],
            cargo_type=data.get('cargo_type', 'MEDICINE'),
            cargo_priority=data.get('cargo_priority', 'CRITICAL'),
            weight_kg=data.get('weight_kg', 500.0)
        )

        risk_score = risk_result.get('risk_score', 25)
        risk_level = risk_result.get('risk_level', RiskLevel.SAFE)
        risk_summary = risk_result.get('risk_summary', '')
        risk_factors = risk_result.get('risk_factors', [])
        recommended_route = risk_result.get('recommended_route', f"{data['origin']} to {data['destination']}")
        safety_advisory = risk_result.get('safety_advisory', 'Drive with caution.')

        # 4. Generate pure SVG QR Code for Driver Handheld / PWA Scan
        # The QR payload contains a structured verification URI
        qr_payload = f"RESQROUTE:TRIP:{qr_token}:{shipment_code}"
        qr_svg = generate_qr_svg(qr_payload)

        # 5. Create Shipment Record
        shipment = Shipment.objects.create(
            shipment_code=shipment_code,
            customer=customer,
            cargo_type=data.get('cargo_type'),
            cargo_priority=data.get('cargo_priority'),
            origin=data.get('origin'),
            destination=data.get('destination'),
            weight_kg=data.get('weight_kg', 500.0),
            delivery_address=data.get('delivery_address', ''),
            special_instructions=data.get('special_instructions', ''),
            is_emergency_relief=data.get('is_emergency_relief', True),
            status=ShipmentStatus.READY,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_summary=risk_summary,
            risk_factors=risk_factors,
            recommended_route=recommended_route,
            qr_token=qr_token,
            qr_svg=qr_svg
        )

        # 6. Pre-create associated Trip pending Driver QR Activation
        trip_code = f"TRIP-{shipment_code.split('-')[-1]}"
        Trip.objects.create(
            trip_code=trip_code,
            shipment=shipment,
            status=TripStatus.READY,
            current_corridor_segment=f"{data['origin']} (Outskirts Base)",
            route_advisory=safety_advisory
        )

        response_serializer = ShipmentSerializer(shipment)
        return Response({
            'message': 'Corridor Shipment successfully requisitioned with AI Risk Assessment.',
            'shipment': response_serializer.data,
            'ai_evaluation': risk_result
        }, status=status.HTTP_201_CREATED)


class ShipmentDetailView(views.APIView):
    """Retrieve details and QR badge for a specific shipment."""
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request, code):
        shipment = Shipment.objects.filter(shipment_code__iexact=code).select_related('customer', 'trip').first()
        if not shipment:
            shipment = Shipment.objects.filter(qr_token__iexact=code).select_related('customer', 'trip').first()
        if not shipment:
            return Response({'detail': f"Shipment '{code}' not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ShipmentSerializer(shipment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TripActivateView(views.APIView):
    """
    Driver activates trip using scanned QR Code token or shipment code.
    Changes Trip to ACTIVE and Shipment to IN_TRANSIT.
    """
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TripActivateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        raw_token = serializer.validated_data['qr_token'].strip()
        vehicle_number = serializer.validated_data.get('vehicle_number', 'TR-102')

        # Handle parsed payload like "RESQROUTE:TRIP:<token>:<code\>" or direct token/code
        clean_token = raw_token
        if raw_token.startswith('RESQROUTE:TRIP:'):
            parts = raw_token.split(':')
            if len(parts) >= 3:
                clean_token = parts[2]

        shipment = (
            Shipment.objects.filter(qr_token__iexact=clean_token).select_related('trip').first()
            or Shipment.objects.filter(shipment_code__iexact=clean_token).select_related('trip').first()
        )

        if not shipment:
            # Check if clean_token matches trip_code
            trip = Trip.objects.filter(trip_code__iexact=clean_token).select_related('shipment').first()
            if trip:
                shipment = trip.shipment

        if not shipment:
            return Response({
                'detail': f"Invalid or unrecognized QR token: '{raw_token}'. Please scan a valid ResQRoute dispatch badge."
            }, status=status.HTTP_404_NOT_FOUND)

        trip = getattr(shipment, 'trip', None)
        if not trip:
            trip = Trip.objects.create(
                trip_code=f"TRIP-{shipment.shipment_code.split('-')[-1]}",
                shipment=shipment,
                status=TripStatus.READY,
                current_corridor_segment=f"{shipment.origin} (Base)"
            )

        # Mark Trip as ACTIVE
        trip.status = TripStatus.ACTIVE
        trip.vehicle_number = vehicle_number
        trip.activated_at = timezone.now()
        trip.last_ping_at = timezone.now()
        
        # Link driver if authenticated
        if request.user.is_authenticated and request.user.role == 'DRIVER':
            trip.driver = request.user
        elif not trip.driver:
            driver_user = User.objects.filter(role='DRIVER').first()
            if driver_user:
                trip.driver = driver_user

        trip.save()

        # Update shipment status
        shipment.status = ShipmentStatus.IN_TRANSIT
        shipment.save()

        trip_serializer = TripSerializer(trip)
        return Response({
            'message': f"Trip {trip.trip_code} successfully activated for Shipment {shipment.shipment_code}!",
            'trip': trip_serializer.data
        }, status=status.HTTP_200_OK)


class TripStatusUpdateView(views.APIView):
    """Update trip transit status (e.g. IN_TRANSIT, COMPLETED)."""
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request, trip_code):
        trip = Trip.objects.filter(trip_code__iexact=trip_code).select_related('shipment', 'driver').first()
        if not trip:
            return Response({'detail': f"Trip '{trip_code}' not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TripStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']
        segment = serializer.validated_data.get('current_corridor_segment')

        trip.status = new_status
        trip.last_ping_at = timezone.now()
        if segment:
            trip.current_corridor_segment = segment

        if new_status == TripStatus.COMPLETED:
            trip.completed_at = timezone.now()
            trip.shipment.status = ShipmentStatus.DELIVERED
            trip.shipment.save()
        elif new_status == TripStatus.IN_TRANSIT:
            trip.shipment.status = ShipmentStatus.IN_TRANSIT
            trip.shipment.save()

        trip.save()
        return Response({
            'message': f"Trip {trip.trip_code} status updated to {new_status}.",
            'trip': TripSerializer(trip).data
        }, status=status.HTTP_200_OK)


class DriverActiveTripsView(views.APIView):
    """List active / pending trips for driver interface."""
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        trips = Trip.objects.all().select_related('shipment', 'driver').order_by('-activated_at', '-created_at')
        serializer = TripSerializer(trips, many=True)
        return Response({
            'count': trips.count(),
            'trips': serializer.data
        }, status=status.HTTP_200_OK)


class RouteRiskEvaluateView(views.APIView):
    """
    On-demand AI route risk simulation without committing to a shipment.
    Evaluates hazards using OpenAI gpt-4o-mini + North East terrain model.
    """
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RouteRiskEvaluateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        result = evaluate_corridor_risk(
            origin=data['origin'],
            destination=data['destination'],
            cargo_type=data.get('cargo_type', 'MEDICINE'),
            cargo_priority=data.get('cargo_priority', 'CRITICAL'),
            weight_kg=data.get('weight_kg', 500.0)
        )
        return Response(result, status=status.HTTP_200_OK)
