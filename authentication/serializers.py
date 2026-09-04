from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    User, 
    UserRole, 
    DriverProfile, 
    CustomerProfile, 
    AuthorityProfile, 
    ApprovalStatus, 
    AreaType
)


class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = (
            'id',
            'vehicle_type',
            'vehicle_number',
            'license_number',
            'license_issuing_state',
            'license_expiry',
            'is_available',
            'is_verified'
        )


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = (
            'id',
            'area_type',
            'locality_name',
            'pincode',
            'state',
            'department',
            'delivery_address'
        )


class AuthorityProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorityProfile
        fields = (
            'id',
            'official_id',
            'designation',
            'department_name',
            'jurisdiction_state',
            'office_address',
            'approval_status',
            'approved_at'
        )


class UserProfileSerializer(serializers.ModelSerializer):
    driver_profile = DriverProfileSerializer(read_only=True)
    customer_profile = CustomerProfileSerializer(read_only=True)
    authority_profile = AuthorityProfileSerializer(read_only=True)

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
            'authority_profile',
            'date_joined'
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    
    # Customer specific fields
    area_type = serializers.CharField(write_only=True, required=False, allow_blank=True)
    locality_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    pincode = serializers.CharField(write_only=True, required=False, allow_blank=True)
    state = serializers.CharField(write_only=True, required=False, allow_blank=True)
    delivery_address = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Driver specific fields
    vehicle_type = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vehicle_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    license_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    license_issuing_state = serializers.CharField(write_only=True, required=False, allow_blank=True)
    license_expiry = serializers.DateField(write_only=True, required=False, allow_null=True)

    # Authority / Admin specific fields
    official_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    designation = serializers.CharField(write_only=True, required=False, allow_blank=True)
    department_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    jurisdiction_state = serializers.CharField(write_only=True, required=False, allow_blank=True)
    office_address = serializers.CharField(write_only=True, required=False, allow_blank=True)

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
            # Customer
            'area_type',
            'locality_name',
            'pincode',
            'state',
            'delivery_address',
            # Driver
            'vehicle_type',
            'vehicle_number',
            'license_number',
            'license_issuing_state',
            'license_expiry',
            # Authority
            'official_id',
            'designation',
            'department_name',
            'jurisdiction_state',
            'office_address',
        )

    def to_internal_value(self, data):
        import re
        if 'username' in data and isinstance(data['username'], str):
            mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
            mutable_data['username'] = re.sub(r'\s+', '_', mutable_data['username'].strip()).lower()
            data = mutable_data
        return super().to_internal_value(data)

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(f"Username '{value}' is already registered. Please choose another.")
        return value

    def validate_email(self, value):
        if value:
            clean_email = value.strip().lower()
            if User.objects.filter(email__iexact=clean_email).exists():
                raise serializers.ValidationError("An account with this email address already exists.")
            return clean_email
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        role = attrs.get('role', UserRole.CUSTOMER)

        if role == UserRole.CUSTOMER:
            if not attrs.get('email'):
                raise serializers.ValidationError({"email": "Email address is required for Customer registration."})
            if not attrs.get('locality_name'):
                raise serializers.ValidationError({"locality_name": "City or Village name is required."})
            if not attrs.get('pincode'):
                raise serializers.ValidationError({"pincode": "Pincode is required."})
            if not attrs.get('state'):
                raise serializers.ValidationError({"state": "Please select your North Eastern state."})

        elif role == UserRole.DRIVER:
            if not attrs.get('phone_number'):
                raise serializers.ValidationError({"phone_number": "Phone number is required for Field Drivers."})
            if not attrs.get('vehicle_number'):
                raise serializers.ValidationError({"vehicle_number": "Vehicle identifier is required (e.g. TR-102)."})
            if not attrs.get('license_number'):
                raise serializers.ValidationError({"license_number": "Driving license number is required (e.g. TN01 20190001234)."})

        elif role == UserRole.ADMIN:
            if not attrs.get('email'):
                raise serializers.ValidationError({"email": "Official government email is required."})
            if not attrs.get('official_id'):
                raise serializers.ValidationError({"official_id": "Government Employee ID or Service Badge Code is required."})
            if not attrs.get('designation'):
                raise serializers.ValidationError({"designation": "Official government designation / title is required."})
            if not attrs.get('department_name'):
                raise serializers.ValidationError({"department_name": "Department or Ministry name is required."})
            if not attrs.get('jurisdiction_state'):
                raise serializers.ValidationError({"jurisdiction_state": "Jurisdiction state is required."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        # Pop role-specific fields
        # Customer
        area_type = validated_data.pop('area_type', AreaType.CITY)
        locality_name = validated_data.pop('locality_name', '')
        pincode = validated_data.pop('pincode', '')
        state = validated_data.pop('state', '')
        delivery_address = validated_data.pop('delivery_address', '')

        # Driver
        vehicle_type = validated_data.pop('vehicle_type', 'Heavy Emergency Truck')
        vehicle_number = validated_data.pop('vehicle_number', '')
        license_number = validated_data.pop('license_number', '')
        license_issuing_state = validated_data.pop('license_issuing_state', '')
        license_expiry = validated_data.pop('license_expiry', None)

        # Authority
        official_id = validated_data.pop('official_id', '')
        designation = validated_data.pop('designation', '')
        department_name = validated_data.pop('department_name', '')
        jurisdiction_state = validated_data.pop('jurisdiction_state', '')
        office_address = validated_data.pop('office_address', '')

        password = validated_data.pop('password')

        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                **validated_data
            )

            if user.role == UserRole.CUSTOMER:
                CustomerProfile.objects.create(
                    user=user,
                    area_type=area_type,
                    locality_name=locality_name,
                    pincode=pincode,
                    state=state,
                    delivery_address=delivery_address
                )
            elif user.role == UserRole.DRIVER:
                DriverProfile.objects.create(
                    user=user,
                    vehicle_type=vehicle_type or 'Heavy Emergency Truck',
                    vehicle_number=vehicle_number,
                    license_number=license_number,
                    license_issuing_state=license_issuing_state,
                    license_expiry=license_expiry
                )
            elif user.role == UserRole.ADMIN:
                AuthorityProfile.objects.create(
                    user=user,
                    official_id=official_id,
                    designation=designation,
                    department_name=department_name,
                    jurisdiction_state=jurisdiction_state,
                    office_address=office_address,
                    approval_status=ApprovalStatus.PENDING
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

        # Government Officials cannot log in directly until approved by Superadmin
        if user.role == UserRole.ADMIN and not user.is_superuser:
            auth_prof = getattr(user, 'authority_profile', None)
            if not auth_prof or auth_prof.approval_status != ApprovalStatus.APPROVED:
                raise serializers.ValidationError({
                    "detail": "Your Government Official / Authority account is pending verification by Superadmin. You will be able to access corridor reports once approved."
                })

        # If specific role requested for login portal check (optional enforcement)
        if role and user.role != role and not user.is_staff and not user.is_superuser:
            raise serializers.ValidationError({
                "detail": f"This account is registered as a {user.get_role_display()}, not {role}."
            })

        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
