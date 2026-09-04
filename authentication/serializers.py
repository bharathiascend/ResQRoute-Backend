from django.db import transaction
from django.contrib.auth import authenticate
import secrets
import string
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    User, 
    UserRole, 
    DriverProfile, 
    CustomerProfile, 
    AuthorityProfile, 
    ApprovalStatus, 
    AreaType,
    OfficialPasswordResetRequest
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
            'state',
            'district',
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
            'district',
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
            'district_office',
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
    district = serializers.CharField(write_only=True, required=False, allow_blank=True)
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
    district_office = serializers.CharField(write_only=True, required=False, allow_blank=True)
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
            'district',
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
            'district_office',
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
        district = validated_data.pop('district', '')
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
        district_office = validated_data.pop('district_office', '')
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
                    district=district,
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
                    license_expiry=license_expiry,
                    state=state,
                    district=district
                )
            elif user.role == UserRole.ADMIN:
                AuthorityProfile.objects.create(
                    user=user,
                    official_id=official_id or f"OFFICIAL-{user.id:04d}",
                    designation=designation,
                    department_name=department_name,
                    jurisdiction_state=jurisdiction_state,
                    district_office=district_office,
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


class ForgotPasswordSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRole.choices)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    official_id = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        role = attrs.get('role')
        if role == UserRole.DRIVER:
            phone = attrs.get('phone_number')
            if not phone:
                raise serializers.ValidationError({"phone_number": "Please provide your registered mobile number."})
            clean_digits = ''.join(filter(str.isdigit, phone))
            if len(clean_digits) < 8:
                raise serializers.ValidationError({"phone_number": "Please enter a valid mobile number."})
            user = User.objects.filter(role=UserRole.DRIVER, phone_number__icontains=clean_digits[-10:]).first()
            if not user:
                raise serializers.ValidationError({"phone_number": f"No driver account found with mobile number '{phone}'."})
            attrs['user'] = user

        elif role == UserRole.CUSTOMER:
            email = attrs.get('email')
            if not email:
                raise serializers.ValidationError({"email": "Please provide your registered Gmail / Email address."})
            clean_email = email.strip().lower()
            user = User.objects.filter(role=UserRole.CUSTOMER, email__iexact=clean_email).first()
            if not user:
                raise serializers.ValidationError({"email": f"No customer account found with email '{email}'."})
            attrs['user'] = user

        elif role == UserRole.ADMIN:
            official_id = attrs.get('official_id')
            email = attrs.get('email')
            user = None
            if official_id:
                auth_prof = AuthorityProfile.objects.filter(official_id__iexact=official_id.strip()).first()
                if auth_prof:
                    user = auth_prof.user
            if not user and email:
                user = User.objects.filter(role=UserRole.ADMIN, email__iexact=email.strip().lower()).first()
            if not user:
                raise serializers.ValidationError({"official_id": "No official account found with the provided Badge Code or Email."})
            attrs['user'] = user

        return attrs

    def save(self):
        role = self.validated_data['role']
        user = self.validated_data['user']

        if role in [UserRole.DRIVER, UserRole.CUSTOMER]:
            prefix = "Drv#" if role == UserRole.DRIVER else "Cust#"
            random_num = ''.join(secrets.choice(string.digits) for _ in range(6))
            temp_password = f"{prefix}{random_num}"
            user.set_password(temp_password)
            user.save()

            if role == UserRole.DRIVER:
                return {
                    "status": "success",
                    "role": role,
                    "target": user.phone_number,
                    "channel": "SMS",
                    "temp_password": temp_password,
                    "message": f"Auto-generated password sent via SMS to mobile number {user.phone_number}. You can now sign in and update your password in your driver dashboard."
                }
            else:
                return {
                    "status": "success",
                    "role": role,
                    "target": user.email,
                    "channel": "EMAIL",
                    "temp_password": temp_password,
                    "message": f"Auto-generated password sent to {user.email}. Check your inbox, sign in, and update your password in your customer dashboard."
                }

        elif role == UserRole.ADMIN:
            req, created = OfficialPasswordResetRequest.objects.get_or_create(
                user=user,
                status=ApprovalStatus.PENDING,
                defaults={
                    'official_id': getattr(getattr(user, 'authority_profile', None), 'official_id', self.validated_data.get('official_id', 'N/A')),
                    'email': user.email or '',
                    'reason': self.validated_data.get('reason', 'Password reset requested via portal')
                }
            )
            return {
                "status": "pending_superadmin",
                "role": role,
                "target": user.username,
                "channel": "SUPERADMIN",
                "temp_password": None,
                "message": "Password reset request submitted. Superadmin will verify your official badge and issue a new credential."
            }


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs.get('current_password')):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        if attrs.get('new_password') != attrs.get('confirm_new_password'):
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class OfficialPasswordResetRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()

    class Meta:
        model = OfficialPasswordResetRequest
        fields = (
            'id',
            'username',
            'full_name',
            'official_id',
            'email',
            'designation',
            'department',
            'state',
            'reason',
            'status',
            'temp_password',
            'requested_at',
            'resolved_at'
        )

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_designation(self, obj):
        return getattr(getattr(obj.user, 'authority_profile', None), 'designation', 'Government Official')

    def get_department(self, obj):
        return getattr(getattr(obj.user, 'authority_profile', None), 'department_name', 'MDoNER / Government Agency')

    def get_state(self, obj):
        return getattr(getattr(obj.user, 'authority_profile', None), 'jurisdiction_state', 'North Eastern Corridor')

