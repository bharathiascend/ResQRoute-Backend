from django.db import connection
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
)


class HealthCheckView(APIView):
    """
    Health check endpoint satisfying SIH26002 STEP 01 requirement:
    GET /health and GET /api/health/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        db_status = "connected"
        try:
            connection.ensure_connection()
        except Exception as e:
            db_status = f"error: {str(e)}"

        return Response({
            "status": "ok",
            "service": "resqroute-api",
            "database": db_status,
            "database_engine": connection.vendor,
            "database_host": connection.settings_dict.get('HOST') or 'sqlite3'
        }, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    Register a new Customer or Driver with role-based profile creation.
    POST /api/auth/register/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            user_data = UserProfileSerializer(user).data
            return Response({
                "message": f"Successfully registered as {user.get_role_display()}",
                "user": user_data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Authenticate User with username/email and password.
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            access = serializer.validated_data['access']
            refresh = serializer.validated_data['refresh']
            user_data = UserProfileSerializer(user).data
            return Response({
                "message": "Login successful",
                "user": user_data,
                "access": access,
                "refresh": refresh,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    Retrieve current authenticated user profile.
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthorityRequestListView(APIView):
    """
    List government authority registration requests for Superadmin review.
    GET /api/auth/authority-requests/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or request.user.is_staff):
            return Response({"detail": "Only Superadmin can access authority requests."}, status=status.HTTP_403_FORBIDDEN)

        from .models import AuthorityProfile
        authorities = AuthorityProfile.objects.select_related('user', 'approved_by').all().order_by('-created_at')
        
        data = []
        for auth in authorities:
            data.append({
                "id": auth.id,
                "user_id": auth.user.id,
                "username": auth.user.username,
                "full_name": auth.user.get_full_name() or auth.user.username,
                "email": auth.user.email,
                "phone_number": auth.user.phone_number,
                "official_id": auth.official_id,
                "designation": auth.designation,
                "department_name": auth.department_name,
                "jurisdiction_state": auth.jurisdiction_state,
                "office_address": auth.office_address,
                "approval_status": auth.approval_status,
                "approved_by": auth.approved_by.username if auth.approved_by else None,
                "approved_at": auth.approved_at,
                "created_at": auth.created_at,
            })

        return Response(data, status=status.HTTP_200_OK)


class AuthorityApprovalView(APIView):
    """
    Approve or reject a government authority account.
    POST /api/auth/authority-requests/<id>/action/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not (request.user.is_superuser or request.user.is_staff):
            return Response({"detail": "Only Superadmin can approve or reject authority accounts."}, status=status.HTTP_403_FORBIDDEN)

        from django.utils import timezone
        from .models import AuthorityProfile, ApprovalStatus
        try:
            authority = AuthorityProfile.objects.select_related('user').get(pk=pk)
        except AuthorityProfile.DoesNotExist:
            return Response({"detail": "Authority record not found."}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action', 'approve').lower()
        if action == 'approve':
            authority.approval_status = ApprovalStatus.APPROVED
            authority.approved_by = request.user
            authority.approved_at = timezone.now()
            authority.save()
            return Response({
                "message": f"Successfully approved {authority.user.get_full_name() or authority.user.username} as {authority.designation}.",
                "approval_status": authority.approval_status
            }, status=status.HTTP_200_OK)
        elif action == 'reject':
            authority.approval_status = ApprovalStatus.REJECTED
            authority.approved_by = request.user
            authority.approved_at = timezone.now()
            authority.save()
            return Response({
                "message": f"Rejected authority request for {authority.user.get_full_name() or authority.user.username}.",
                "approval_status": authority.approval_status
            }, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid action. Use 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)


class RerouteReportsView(APIView):
    """
    Provide state-wise and district-wise rerouting analytics for government officials.
    GET /api/auth/reroute-reports/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            "total_reroutes_today": 353,
            "active_corridors": 12,
            "critical_weather_alerts": 4,
            "state_wise_reports": [
                {
                    "state": "Assam",
                    "reroute_count": 128,
                    "primary_cause": "Brahmaputra Flood Risk & Dima Hasao Landslide Bypass",
                    "districts_affected": ["Dima Hasao", "Cachar", "Kamrup Metropolitan", "Karbi Anglong"],
                    "active_trucks": 84
                },
                {
                    "state": "Sikkim",
                    "reroute_count": 42,
                    "primary_cause": "North Sikkim NH-10 Highway Blockade & Teesta Basin Diversion",
                    "districts_affected": ["Mangan", "Gangtok", "Pakyong"],
                    "active_trucks": 31
                },
                {
                    "state": "Arunachal Pradesh",
                    "reroute_count": 51,
                    "primary_cause": "Sela Pass High-Altitude Snowfall & Vartak Border Road Maintenance",
                    "districts_affected": ["Tawang", "West Kameng", "Lower Subansiri"],
                    "active_trucks": 27
                },
                {
                    "state": "Manipur",
                    "reroute_count": 38,
                    "primary_cause": "NH-37 Imphal - Jiribam Corridor Alternate Route Optimization",
                    "districts_affected": ["Noney", "Tamenglong", "Imphal West"],
                    "active_trucks": 29
                },
                {
                    "state": "Meghalaya",
                    "reroute_count": 35,
                    "primary_cause": "Shillong Plateau Fog & East Khasi Hills Road Widening",
                    "districts_affected": ["East Khasi Hills", "Ri-Bhoi", "West Jaintia Hills"],
                    "active_trucks": 22
                },
                {
                    "state": "Nagaland",
                    "reroute_count": 26,
                    "primary_cause": "Kohima - Dimapur Bypass Monsoon Rutting Diversion",
                    "districts_affected": ["Kohima", "Dimapur", "Wokha"],
                    "active_trucks": 19
                },
                {
                    "state": "Mizoram",
                    "reroute_count": 19,
                    "primary_cause": "Aizawl - Silchar National Highway Landslip Diversion",
                    "districts_affected": ["Kolasib", "Aizawl", "Lunglei"],
                    "active_trucks": 15
                },
                {
                    "state": "Tripura",
                    "reroute_count": 14,
                    "primary_cause": "Agartala - Dharmanagar Heavy Rain Flash Flood Warning",
                    "districts_affected": ["West Tripura", "North Tripura", "Dhalai"],
                    "active_trucks": 12
                }
            ],
            "daily_trends": [
                {"day": "Mon", "reroutes": 48},
                {"day": "Tue", "reroutes": 62},
                {"day": "Wed", "reroutes": 54},
                {"day": "Thu", "reroutes": 79},
                {"day": "Fri", "reroutes": 110}
            ],
            "corridor_logs": [
                {
                    "log_id": "RER-SK-2026-081",
                    "from_location": "Siliguri Hub (West Bengal Gateway)",
                    "to_location": "Gangtok Food Supplies Depot",
                    "state": "Sikkim",
                    "district": "Pakyong / Gangtok",
                    "original_route": "NH-10 via Teesta Bazaar",
                    "rerouted_via": "Lava - Algarah - Reshi Alternate Mountain Corridor",
                    "cause": "Flash Flood Warning & Rockfall along 29th Mile",
                    "timestamp": "Today 10:45 AM",
                    "authority_in_charge": "Sikkim SDMA (SSDMA)",
                    "status": "IN_TRANSIT"
                },
                {
                    "log_id": "RER-SK-2026-082",
                    "from_location": "Rangpo Border Checkpost",
                    "to_location": "Mangan Emergency Medical Center",
                    "state": "Sikkim",
                    "district": "Mangan (North Sikkim)",
                    "original_route": "Singtam - Dikchu - Mangan Main Route",
                    "rerouted_via": "Phodong - Kabi Alpine Bypass",
                    "cause": "Sinking zone trigger near Dikchu Hydro Project",
                    "timestamp": "Today 11:20 AM",
                    "authority_in_charge": "BRO Swastik Division",
                    "status": "REROUTED_SUCCESS"
                },
                {
                    "log_id": "RER-AS-2026-104",
                    "from_location": "Guwahati Central Depot",
                    "to_location": "Silchar Civil Hospital Medical Storage",
                    "state": "Assam",
                    "district": "Dima Hasao",
                    "original_route": "NH-27 Lumding - Haflong Expressway",
                    "rerouted_via": "Meghalaya NH-06 Jowai - Ladrymbai Corridor",
                    "cause": "Landslide block at Jatinga Lampu gorge",
                    "timestamp": "Today 08:30 AM",
                    "authority_in_charge": "Assam SDMA & NDRF 1st Bn",
                    "status": "REROUTED_SUCCESS"
                },
                {
                    "log_id": "RER-AR-2026-057",
                    "from_location": "Tezpur Logistics Base",
                    "to_location": "Tawang Army Forward Base Supplies",
                    "state": "Arunachal Pradesh",
                    "district": "Tawang & West Kameng",
                    "original_route": "Bhalukpong - Bomdila - Sela Pass",
                    "rerouted_via": "Sela Tunnel Emergency Relief Bypass",
                    "cause": "Sudden heavy blizzard & zero-visibility icing on pass",
                    "timestamp": "Today 09:15 AM",
                    "authority_in_charge": "BRO Project Vartak",
                    "status": "IN_TRANSIT"
                },
                {
                    "log_id": "RER-ML-2026-039",
                    "from_location": "Guwahati Khanapara",
                    "to_location": "Shillong Civil Hospital Oxygen Store",
                    "state": "Meghalaya",
                    "district": "Ri-Bhoi / East Khasi Hills",
                    "original_route": "GS Road Highway 6",
                    "rerouted_via": "Umiam Bypass - Mawlai Western Bypass",
                    "cause": "Dense hill fog and fuel tanker spill near Nongpoh",
                    "timestamp": "Today 07:50 AM",
                    "authority_in_charge": "Meghalaya Police Highway Patrol",
                    "status": "REROUTED_SUCCESS"
                }
            ]
        }
        return Response(data, status=status.HTTP_200_OK)

