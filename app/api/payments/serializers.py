from rest_framework import serializers
from .models import Payment, ParkPoints, PointsTransaction

class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'reservation',
            'points_amount',
            'status',
            'transaction',
            'error_message',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'transaction',
            'error_message',
            'created_at',
            'updated_at'
        ]

class CreatePaymentSerializer(serializers.Serializer):
    """Serializer for creating a payment."""
    
    reservation_id = serializers.IntegerField()

class RefundPaymentSerializer(serializers.Serializer):
    """Serializer for refunding a payment."""
    
    payment_id = serializers.IntegerField()

class ParkPointsSerializer(serializers.ModelSerializer):
    """Serializer for ParkPoints model."""
    
    class Meta:
        model = ParkPoints
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PointsTransaction model."""
    
    class Meta:
        model = PointsTransaction
        fields = [
            'id',
            'points',
            'amount',
            'transaction_type',
            'description',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at'] 