from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from app.api.parking_lots.models import ParkingLot, ParkingSpace
from decimal import Decimal

User = get_user_model()

class Reservation(models.Model):
    """Model for parking reservations."""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    parking_space = models.ForeignKey(
        ParkingSpace,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    vehicle_plate = models.CharField(_('vehicle plate'), max_length=20)
    notes = models.TextField(_('notes'), blank=True)
    start_time = models.DateTimeField(_('start time'))
    end_time = models.DateTimeField(_('end time'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('reservation')
        verbose_name_plural = _('reservations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reservation {self.id} - {self.user.get_full_name()}"
    
    @property
    def duration(self):
        """Calculate the duration of the reservation in hours."""
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            return Decimal(str(duration.total_seconds() / 3600))  # Convert to hours and to Decimal
        return Decimal('0')
    
    @property
    def total_cost(self):
        """Calculate the total cost of the reservation."""
        return self.duration * self.parking_lot.hourly_rate
    
    def save(self, *args, **kwargs):
        """Override save to handle space status updates and validation."""
        is_new = self._state.adding
        
        if is_new:
            # Validate time range
            if self.end_time <= self.start_time:
                raise ValueError("End time must be after start time")
            
            # Check for overlapping reservations
            overlapping = Reservation.objects.filter(
                parking_space=self.parking_space,
                status=self.Status.ACTIVE,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exists()
            
            if overlapping:
                raise ValueError("This space is already reserved for the selected time period")
            
            # Update parking lot available spaces first
            self.parking_lot.available_spaces = self.parking_lot.available_spaces - 1
            self.parking_lot.save()
            
            # Then update parking space status
            self.parking_space.status = ParkingSpace.Status.RESERVED
            self.parking_space.current_user = self.user
            self.parking_space.save()
            
        elif self.status == self.Status.CANCELLED:
            # Update parking lot available spaces first
            self.parking_lot.available_spaces = self.parking_lot.available_spaces + 1
            self.parking_lot.save()
            
            # Then update parking space status
            self.parking_space.status = ParkingSpace.Status.AVAILABLE
            self.parking_space.current_user = None
            self.parking_space.save()
        
        super().save(*args, **kwargs)
