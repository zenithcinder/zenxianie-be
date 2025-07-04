from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from app.api.parking_lots.models import ParkingLot
from app.api.reservations.models import Reservation
from datetime import datetime
from django.core.exceptions import ValidationError
from .validators import (
    validate_non_negative, validate_positive, validate_percentage,
    validate_month, validate_year, validate_future_date, validate_peak_day
)

User = get_user_model()

class DailyReport(models.Model):
    """Model for daily parking reports."""
    
    date = models.DateField(_('date'), unique=True, validators=[validate_future_date])
    total_revenue = models.DecimalField(
        _('total revenue'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[validate_non_negative]
    )
    total_reservations = models.PositiveIntegerField(
        _('total reservations'),
        default=0
    )
    average_duration = models.FloatField(
        _('average duration'),
        default=0,
        validators=[validate_non_negative]
    )
    peak_hour = models.TimeField(_('peak hour'), null=True)
    occupancy_rate = models.FloatField(
        _('occupancy rate'),
        default=0,
        validators=[validate_percentage]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('daily report')
        verbose_name_plural = _('daily reports')
        ordering = ['-date']
    
    def __str__(self):
        return f"Daily Report - {self.date}"
    
    def clean(self):
        """Additional validation for the model."""
        super().clean()
        if self.peak_hour and not isinstance(self.peak_hour, datetime.time):
            raise ValidationError({'peak_hour': 'Invalid time format.'})
    
    @classmethod
    def generate_report(cls, date):
        """Generate a daily report for the specified date."""
        # Get all reservations for the date
        reservations = Reservation.objects.filter(
            start_time__date=date,
            status__in=['active', 'completed']
        )
        
        # Calculate total revenue
        total_revenue = sum(reservation.total_cost for reservation in reservations)
        
        # Calculate total reservations
        total_reservations = reservations.count()
        
        # Calculate average duration
        durations = [reservation.duration for reservation in reservations]
        average_duration = sum(durations) / len(durations) if durations else 0
        
        # Find peak hour
        hourly_counts = {}
        for reservation in reservations:
            hour = reservation.start_time.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None
        if peak_hour is not None:
            peak_hour = datetime.strptime(f"{peak_hour:02d}:00", "%H:%M").time()
        
        # Calculate overall occupancy rate
        total_spaces = sum(lot.total_spaces for lot in ParkingLot.objects.all())
        occupied_spaces = sum(lot.total_spaces - lot.available_spaces for lot in ParkingLot.objects.all())
        occupancy_rate = (occupied_spaces / total_spaces * 100) if total_spaces > 0 else 0
        
        # Create or update report
        report, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'total_revenue': total_revenue,
                'total_reservations': total_reservations,
                'average_duration': average_duration,
                'peak_hour': peak_hour,
                'occupancy_rate': occupancy_rate
            }
        )
        
        return report

class MonthlyReport(models.Model):
    """Model for monthly parking reports."""
    
    year = models.PositiveIntegerField(_('year'), validators=[validate_year])
    month = models.PositiveIntegerField(_('month'), validators=[validate_month])
    total_revenue = models.DecimalField(
        _('total revenue'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[validate_non_negative]
    )
    total_reservations = models.PositiveIntegerField(
        _('total reservations'),
        default=0
    )
    average_duration = models.FloatField(
        _('average duration'),
        default=0,
        validators=[validate_non_negative]
    )
    average_occupancy_rate = models.FloatField(
        _('average occupancy rate'),
        default=0,
        validators=[validate_percentage]
    )
    peak_day = models.DateField(_('peak day'), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('monthly report')
        verbose_name_plural = _('monthly reports')
        ordering = ['-year', '-month']
        unique_together = ['year', 'month']
    
    def __str__(self):
        return f"Monthly Report - {self.year}/{self.month}"
    
    def clean(self):
        """Additional validation for the model."""
        super().clean()
        if self.peak_day:
            validate_peak_day(self.peak_day, self.year, self.month)
    
    @classmethod
    def generate_report(cls, year, month):
        """Generate a monthly report for the specified year and month."""
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        
        # Get all reservations for the month
        reservations = Reservation.objects.filter(
            start_time__year=year,
            start_time__month=month,
            status__in=['active', 'completed']
        )
        
        # Calculate total revenue
        total_revenue = sum(reservation.total_cost for reservation in reservations)
        
        # Calculate total reservations
        total_reservations = reservations.count()
        
        # Calculate average duration
        durations = [reservation.duration for reservation in reservations]
        average_duration = sum(durations) / len(durations) if durations else 0
        
        # Calculate average occupancy rate
        daily_reports = DailyReport.objects.filter(
            date__year=year,
            date__month=month
        )
        average_occupancy_rate = sum(report.occupancy_rate for report in daily_reports) / len(daily_reports) if daily_reports else 0
        
        # Find peak day
        daily_counts = {}
        for reservation in reservations:
            day = reservation.start_time.date()
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        peak_day = max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else None
        
        # Create or update report
        report, created = cls.objects.update_or_create(
            year=year,
            month=month,
            defaults={
                'total_revenue': total_revenue,
                'total_reservations': total_reservations,
                'average_duration': average_duration,
                'average_occupancy_rate': average_occupancy_rate,
                'peak_day': peak_day
            }
        )
        
        return report

class ParkingLotReport(models.Model):
    """Model for parking lot specific reports."""
    
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    date = models.DateField(_('date'), validators=[validate_future_date])
    total_revenue = models.DecimalField(
        _('total revenue'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[validate_non_negative]
    )
    total_reservations = models.PositiveIntegerField(
        _('total reservations'),
        default=0
    )
    occupancy_rate = models.FloatField(
        _('occupancy rate'),
        default=0,
        validators=[validate_percentage]
    )
    average_duration = models.FloatField(
        _('average duration'),
        default=0,
        validators=[validate_non_negative]
    )
    peak_hour = models.TimeField(_('peak hour'), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('parking lot report')
        verbose_name_plural = _('parking lot reports')
        ordering = ['-date', 'parking_lot']
        unique_together = ['parking_lot', 'date']
    
    def __str__(self):
        return f"{self.parking_lot.name} - {self.date}"
    
    def clean(self):
        """Additional validation for the model."""
        super().clean()
        if self.peak_hour and not isinstance(self.peak_hour, datetime.time):
            raise ValidationError({'peak_hour': 'Invalid time format.'})
        if not ParkingLot.objects.filter(id=self.parking_lot.id).exists():
            raise ValidationError({'parking_lot': 'Parking lot does not exist.'})
    
    @classmethod
    def generate_report(cls, parking_lot, date):
        """Generate a report for a specific parking lot and date."""
        # Get all reservations for the parking lot and date
        reservations = Reservation.objects.filter(
            parking_lot=parking_lot,
            start_time__date=date,
            status__in=['active', 'completed']
        )
        
        # Calculate total revenue
        total_revenue = sum(reservation.total_cost for reservation in reservations)
        
        # Calculate total reservations
        total_reservations = reservations.count()
        
        # Calculate occupancy rate
        occupancy_rate = ((parking_lot.total_spaces - parking_lot.available_spaces) / parking_lot.total_spaces * 100) if parking_lot.total_spaces > 0 else 0
        
        # Calculate average duration
        durations = [reservation.duration for reservation in reservations]
        average_duration = sum(durations) / len(durations) if durations else 0
        
        # Find peak hour
        hourly_counts = {}
        for reservation in reservations:
            hour = reservation.start_time.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None
        if peak_hour is not None:
            peak_hour = datetime.strptime(f"{peak_hour:02d}:00", "%H:%M").time()
        
        # Create or update report
        report, created = cls.objects.update_or_create(
            parking_lot=parking_lot,
            date=date,
            defaults={
                'total_revenue': total_revenue,
                'total_reservations': total_reservations,
                'occupancy_rate': occupancy_rate,
                'average_duration': average_duration,
                'peak_hour': peak_hour
            }
        )
        
        return report 