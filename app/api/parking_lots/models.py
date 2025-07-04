from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class ParkingLot(models.Model):
    """Model for parking lots."""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        MAINTENANCE = 'maintenance', _('Maintenance')
        CLOSED = 'closed', _('Closed')
    
    name = models.CharField(_('name'), max_length=100)
    address = models.TextField(_('address'))
    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6)
    total_spaces = models.PositiveIntegerField(_('total spaces'))
    available_spaces = models.PositiveIntegerField(_('available spaces'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    hourly_rate = models.DecimalField(_('hourly rate'), max_digits=6, decimal_places=2)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_parking_lots',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('parking lot')
        verbose_name_plural = _('parking lots')
    
    def __str__(self):
        return self.name
    
    @property
    def occupancy_rate(self):
        """Calculate the occupancy rate of the parking lot."""
        if self.total_spaces == 0:
            return 0
        return ((self.total_spaces - self.available_spaces) / self.total_spaces) * 100

class ParkingSpace(models.Model):
    """Model for individual parking spaces within a lot."""
    
    class Status(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        OCCUPIED = 'occupied', _('Occupied')
        RESERVED = 'reserved', _('Reserved')
        MAINTENANCE = 'maintenance', _('Maintenance')
    
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name='spaces'
    )
    space_number = models.CharField(_('space number'), max_length=10)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )
    current_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='occupied_spaces'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('parking space')
        verbose_name_plural = _('parking spaces')
        unique_together = ('parking_lot', 'space_number')
    
    def __str__(self):
        return f"{self.parking_lot.name} - Space {self.space_number}"
