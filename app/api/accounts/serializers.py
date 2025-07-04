from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data."""
    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Use the default password hasher
        user.save()
        return user

    def update(self, instance, validated_data):
        if 'role' in validated_data:
            if validated_data['role'] == 'admin':
                instance.is_staff = True
            else:
                instance.is_staff = False
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])  # Hash the password
            validated_data.pop('password')
        return super().update(instance, validated_data)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'first_name', 'last_name', 
                 'role', 'status', 'avatar_url', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'password': {'write_only': True},
            'is_staff': {'write_only': True}
        }

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 
                 'first_name', 'last_name')
        read_only_fields = ('role', 'is_staff', 'is_superuser')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Remove any attempts to set restricted fields
        restricted_fields = ['role', 'is_staff', 'is_superuser']
        for field in restricted_fields:
            if field in attrs:
                raise serializers.ValidationError(
                    {field: f"SECURITY ALERT: Unauthorized attempt to modify {field}. This field is restricted and can only be modified by administrators."}
                )
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        # Force role to be USER for new registrations
        validated_data['role'] = User.Role.USER
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        user = User.objects.create_user(**validated_data)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user data."""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'avatar_url')
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ('id', 'user', 'phone_number', 'address', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

class ProfileSerializer(serializers.ModelSerializer):
    # User fields
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    status = serializers.CharField(source='user.status', read_only=True)
    avatar_url = serializers.URLField(source='user.avatar_url', read_only=True)
    created_at = serializers.DateTimeField(source='user.created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='user.updated_at', read_only=True)
    
    class Meta:
        model = Profile
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 
                 'status', 'avatar_url', 'phone_number', 'address', 'created_at', 
                 'updated_at')
        read_only_fields = ('id', 'email', 'username', 'first_name', 'last_name', 
                          'role', 'status', 'avatar_url', 'created_at', 'updated_at') 