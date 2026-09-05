import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from logistics.models import Shipment, Trip, CargoType, CargoPriority, ShipmentStatus, TripStatus, RiskLevel
from logistics.ai_risk_engine import evaluate_corridor_risk
from logistics.qr_service import generate_qr_svg

User = get_user_model()

def seed():
    customer = User.objects.filter(role='CUSTOMER').first()
    driver = User.objects.filter(role='DRIVER').first()

    if not customer:
        print("No customer found, skipping seed.")
        return

    # Shipment 1: RSQ-101 (Guwahati to Silchar - Active)
    if not Shipment.objects.filter(shipment_code='RSQ-101').exists():
        eval1 = evaluate_corridor_risk('Guwahati Central Medical Hub', 'Silchar Civil Hospital', 'MEDICINE', 'CRITICAL', 650.0)
        qr_token_1 = 'RSQ-101-7F9C2B10'
        qr_svg_1 = generate_qr_svg(f"RESQROUTE:TRIP:{qr_token_1}:RSQ-101")
        
        s1 = Shipment.objects.create(
            shipment_code='RSQ-101',
            customer=customer,
            cargo_type=CargoType.MEDICINE,
            cargo_priority=CargoPriority.CRITICAL,
            origin='Guwahati Central Medical Hub',
            destination='Silchar Civil Hospital',
            weight_kg=650.0,
            delivery_address='Civil Hospital Complex, Premtala, Silchar, Cachar, Assam - 788001',
            special_instructions='Temperature-sensitive anti-venom & cholera vaccines. Maintain cold-chain storage at 2-8°C.',
            status=ShipmentStatus.READY,
            is_emergency_relief=True,
            risk_score=eval1.get('risk_score', 28),
            risk_level=eval1.get('risk_level', RiskLevel.SAFE),
            risk_summary=eval1.get('risk_summary', 'Corridor open with light mountain mist. High priority dispatch recommended.'),
            risk_factors=eval1.get('risk_factors', ['Moderate curve grades on NH-6 Meghalaya ridge', 'Clear weather forecast at Lumshnong']),
            recommended_route=eval1.get('recommended_route', 'NH-6 via Lumshnong - Sonapur Tunnel Bypass'),
            qr_token=qr_token_1,
            qr_svg=qr_svg_1
        )
        Trip.objects.create(
            trip_code='TRIP-101',
            shipment=s1,
            driver=driver,
            vehicle_number='AS-01-GC-4921 (TR-101)',
            vehicle_type='Refrigerated Heavy Truck (8W)',
            status=TripStatus.READY,
            current_corridor_segment='Guwahati Central Medical Hub (Dispatched Bay 4)',
            route_advisory=eval1.get('safety_advisory', 'Maintain 40 km/h on wet ridge descents.')
        )
        print("Seeded RSQ-101")

    # Shipment 2: RSQ-102 (Siliguri to Gangtok - Emergency Rations)
    if not Shipment.objects.filter(shipment_code='RSQ-102').exists():
        eval2 = evaluate_corridor_risk('Siliguri Food Relief Base', 'Gangtok District Emergency Store', 'FOOD', 'HIGH', 1200.0)
        qr_token_2 = 'RSQ-102-3D5E8A99'
        qr_svg_2 = generate_qr_svg(f"RESQROUTE:TRIP:{qr_token_2}:RSQ-102")
        
        s2 = Shipment.objects.create(
            shipment_code='RSQ-102',
            customer=customer,
            cargo_type=CargoType.FOOD,
            cargo_priority=CargoPriority.HIGH,
            origin='Siliguri Food Relief Base',
            destination='Gangtok District Emergency Store',
            weight_kg=1200.0,
            delivery_address='District Disaster Relief Store, Development Area, Gangtok, Sikkim - 737101',
            special_instructions='High-energy dry rations & potable drinking water packets for landslide affected zone.',
            status=ShipmentStatus.READY,
            is_emergency_relief=True,
            risk_score=eval2.get('risk_score', 54),
            risk_level=eval2.get('risk_level', RiskLevel.CAUTION),
            risk_summary=eval2.get('risk_summary', 'NH-10 Teesta River corridor experiencing intermittent sliding near 29th Mile. Proceed with convoy escort.'),
            risk_factors=eval2.get('risk_factors', ['Teesta river level elevated', 'Single-lane traffic controlled by BRO at 29th Mile']),
            recommended_route=eval2.get('recommended_route', 'NH-10 via Sevoke - Rangpo or alternate via Lava-Algarah-Reshi'),
            qr_token=qr_token_2,
            qr_svg=qr_svg_2
        )
        Trip.objects.create(
            trip_code='TRIP-102',
            shipment=s2,
            driver=driver,
            vehicle_number='SK-01-D-9982 (TR-102)',
            vehicle_type='Heavy All-Terrain Truck (10W)',
            status=TripStatus.READY,
            current_corridor_segment='Siliguri Hub Exit (Sevoke Corridor)',
            route_advisory=eval2.get('safety_advisory', 'Verify BRO road clearance status at Rangpo border post.')
        )
        print("Seeded RSQ-102")

if __name__ == '__main__':
    seed()
