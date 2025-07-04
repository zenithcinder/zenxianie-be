from rest_framework import serializers
from django.utils import timezone
from .models import Reservation
from app.api.parking_lots.serializers import ParkingSpaceSerializer
from app.api.accounts.serializers import UserSerializer
from django.contrib.auth import get_user_model
from app.api.parking_lots.models import ParkingSpace

User = get_user_model()

class ReservationSerializer(serializers.ModelSerializer):
    """Serializer for reservations."""
    
    duration = serializers.FloatField(read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    parking_lot_name = serializers.CharField(
        source='parking_lot.name',
        read_only=True
    )
    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    user = UserSerializer(read_only=True)
    parking_space = ParkingSpaceSerializer(read_only=True)
    
    class Meta:
        model = Reservation
        fields = (
            'id', 'parking_lot', 'parking_lot_name',
            'parking_space', 'user', 'user_name',
            'vehicle_plate', 'notes', 'start_time',
            'end_time', 'status', 'duration',
            'total_cost', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """Validate reservation data."""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time:
            # Check if end time is after start time
            if end_time <= start_time:
                raise serializers.ValidationError(
                    "End time must be after start time."
                )
            
            # Check if start time is in the future
            if start_time < timezone.now():
                raise serializers.ValidationError(
                    "Start time must be in the future."
                )
            
            # Check if duration is within allowed range (e.g., max 24 hours)
            duration = (end_time - start_time).total_seconds() / 3600
            if duration > 24:
                raise serializers.ValidationError(
                    "Reservation duration cannot exceed 24 hours."
                )
        
        return attrs

class ReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reservations."""
    
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Reservation
        fields = (
            'user', 'parking_lot', 'parking_space', 'vehicle_plate',
            'notes', 'start_time', 'end_time'
        )
    
    def validate(self, attrs):
        """Validate reservation creation."""
        request = self.context.get('request')
        if request and not attrs.get('user'):
            attrs['user'] = request.user
            
        parking_space = attrs.get('parking_space')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        parking_lot = attrs.get('parking_lot')
        
        # Validate parking space belongs to the specified parking lot
        if parking_space and parking_lot:
            if parking_space.parking_lot_id != parking_lot.id:
                raise serializers.ValidationError(
                    "The selected parking space does not belong to the specified parking lot."
                )
        
        # Check if space is available
        if parking_space and parking_space.status != ParkingSpace.Status.AVAILABLE:
            raise serializers.ValidationError(
                "This parking space is not available."
            )
        
        # Check for overlapping reservations
        if start_time and end_time and parking_space:
            overlapping = Reservation.objects.filter(
                parking_space=parking_space,
                status=Reservation.Status.ACTIVE,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()
            
            if overlapping:
                raise serializers.ValidationError(
                    "This space is already reserved for the selected time period."
                )
        
        return attrs

class ReservationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating reservations."""
    
    class Meta:
        model = Reservation
        fields = ('vehicle_plate', 'notes', 'start_time', 'end_time', 'status')
    
    def validate(self, attrs):
        """Validate reservation update."""
        if 'status' in attrs and attrs['status'] == 'cancelled':
            # Allow cancellation without other validations
            return attrs
        
        return super().validate(attrs) 