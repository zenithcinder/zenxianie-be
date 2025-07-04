from django.db import models
from django.conf import settings
from app.api.reservations.models import Reservation

class ParkPoints(models.Model):
    """Model for storing user's ParkPoints balance."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='park_points'
    )
    balance = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s ParkPoints: {self.balance}"

class PointsTransaction(models.Model):
    """Model for tracking ParkPoints transactions."""
    
    class TransactionType(models.TextChoices):
        EARN = 'earn', 'Earn'
        SPEND = 'spend', 'Spend'
    
    points = models.ForeignKey(
        ParkPoints,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.IntegerField()
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount} points: {self.description}"

class Payment(models.Model):
    """Model for storing payment information."""
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
    
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    points_amount = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    transaction = models.OneToOneField(
        PointsTransaction,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment'
    )
    error_message = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} for Reservation {self.reservation.id}: {self.status}" 