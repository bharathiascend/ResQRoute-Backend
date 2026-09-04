from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserRole, DriverProfile, CustomerProfile


class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = ('vehicle_number', 'license_number', 'is_available', 'is_verified')


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ('department', 'delivery_address')


class UserProfileSerializer(serializers.ModelSerializer):
    driver_profile = DriverProfileSerializer(read_only=True)
    customer_profile = CustomerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'organization',
            'driver_profile',
            'customer_profile',
            'date_joined'
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    
    # Optional role-specific input fields
    vehicle_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    license_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    department = serializers.CharField(write_only=True, required=False, allow_blank=True)
    delivery_address = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'organization',
            'vehicle_number',
            'license_number',
            'department',
            'delivery_address'
        )

    def validate_username(self, value):
        sanitized = value.strip().replace(' ', '_').lower()
        if len(sanitized) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        if User.objects.filter(username__iexact=sanitized).exists():
            raise serializers.ValidationError(f"Username '{sanitized}' is already taken. Please choose another.")
        return sanitized

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        role = attrs.get('role', UserRole.CUSTOMER)
        if role == UserRole.DRIVER:
            if not attrs.get('vehicle_number'):
                raise serializers.ValidationError({"vehicle_number": "Vehicle number is required for Driver registration."})
            if not attrs.get('license_number'):
                raise serializers.ValidationError({"license_number": "License number is required for Driver registration."})

        # Validate unique email
        email = attrs.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "A user with this email address already exists."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        vehicle_number = validated_data.pop('vehicle_number', '')
        license_number = validated_data.pop('license_number', '')
        department = validated_data.pop('department', '')
        delivery_address = validated_data.pop('delivery_address', '')
        password = validated_data.pop('password')

        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                **validated_data
            )

            if user.role == UserRole.DRIVER:
                DriverProfile.objects.create(
                    user=user,
                    vehicle_number=vehicle_number,
                    license_number=license_number
                )
            elif user.role == UserRole.CUSTOMER:
                CustomerProfile.objects.create(
                    user=user,
                    department=department,
                    delivery_address=delivery_address
                )

            return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')
        role = attrs.get('role')

        # Allow login via username or email
        user = None
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=username_or_email, password=password)

        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials. Please verify your username/email and password."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is inactive."})

        # If specific role requested for login portal check (optional enforcement)
        if role and user.role != role and not user.is_staff:
            raise serializers.ValidationError({
                "detail": f"This account is registered as a {user.get_role_display()}, not {role}."
            })

        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
