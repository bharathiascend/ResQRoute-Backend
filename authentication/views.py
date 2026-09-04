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
            "database": db_status
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
