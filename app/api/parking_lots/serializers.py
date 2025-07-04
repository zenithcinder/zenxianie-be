from rest_framework import serializers
from .models import ParkingLot, ParkingSpace
from app.api.realtime.utils import send_notification_to_all

class ParkingSpaceSerializer(serializers.ModelSerializer):
    """Serializer for parking spaces."""
    
    class Meta:
        model = ParkingSpace
        fields = ('id', 'parking_lot', 'space_number', 'status', 'current_user', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ParkingLotSerializer(serializers.ModelSerializer):
    """Serializer for parking lots."""
    
    spaces = ParkingSpaceSerializer(many=True, read_only=True)
    occupancy_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ParkingLot
        fields = ('id', 'name', 'address', 'latitude', 'longitude',
                 'total_spaces', 'available_spaces', 'status',
                 'hourly_rate', 'spaces', 'occupancy_rate',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """Validate that available_spaces cannot exceed total_spaces."""
        if 'available_spaces' in attrs and 'total_spaces' in attrs:
            if attrs['available_spaces'] > attrs['total_spaces']:
                raise serializers.ValidationError(
                    "Available spaces cannot exceed total spaces."
                )
        return attrs

class ParkingLotCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating parking lots."""
    
    class Meta:
        model = ParkingLot
        fields = ('name', 'address', 'latitude', 'longitude',
                 'total_spaces', 'available_spaces', 'status',
                 'hourly_rate')
    
    def create(self, validated_data):
        """Create a new parking lot and its spaces."""
        parking_lot = ParkingLot.objects.create(**validated_data)
        
        # Create parking spaces
        for i in range(1, parking_lot.total_spaces + 1):
            ParkingSpace.objects.create(
                parking_lot=parking_lot,
                space_number=str(i).zfill(3)
            )
        
        # Send notification to all users about the new parking lot
        send_notification_to_all({
            "type": "new_parking_lot",
            "message": f"New parking lot '{parking_lot.name}' has been added",
            "data": {
                "parking_lot_id": parking_lot.id,
                "name": parking_lot.name,
                "address": parking_lot.address,
                "total_spaces": parking_lot.total_spaces,
                "hourly_rate": str(parking_lot.hourly_rate),
                "status": parking_lot.status
            }
        })
        
        return parking_lot

class ParkingLotUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating parking lots."""
    
    class Meta:
        model = ParkingLot
        fields = ('name', 'address', 'latitude', 'longitude',
                 'total_spaces', 'available_spaces', 'status',
                 'hourly_rate')
    
    def update(self, instance, validated_data):
        """Update parking lot and adjust spaces if total_spaces changes."""
        old_total_spaces = instance.total_spaces
        new_total_spaces = validated_data.get('total_spaces', old_total_spaces)
        
        # Update the parking lot
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Adjust parking spaces if total_spaces changed
        if new_total_spaces != old_total_spaces:
            current_spaces = instance.spaces.count()
            
            if new_total_spaces > old_total_spaces:
                # Add new spaces
                for i in range(current_spaces + 1, new_total_spaces + 1):
                    ParkingSpace.objects.create(
                        parking_lot=instance,
                        space_number=str(i).zfill(3)
                    )
            else:
                # Remove excess spaces
                instance.spaces.filter(
                    space_number__gt=str(new_total_spaces).zfill(3)
                ).delete()
        
        return instance 