from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime

def validate_non_negative(value):
    """Validate that a value is non-negative."""
    if value < 0:
        raise ValidationError('Value must be non-negative.')

def validate_positive(value):
    """Validate that a value is positive."""
    if value <= 0:
        raise ValidationError('Value must be positive.')

def validate_percentage(value):
    """Validate that a value is between 0 and 100."""
    if not 0 <= value <= 100:
        raise ValidationError('Value must be between 0 and 100.')

def validate_month(value):
    """Validate that a month is between 1 and 12."""
    if not 1 <= value <= 12:
        raise ValidationError('Month must be between 1 and 12.')

def validate_year(value):
    """Validate that a year is reasonable."""
    current_year = timezone.now().year
    if not 2000 <= value <= current_year + 5:
        raise ValidationError('Year must be between 2000 and 5 years from now.')

def validate_future_date(value):
    """Validate that a date is not in the future."""
    if value > timezone.now().date():
        raise ValidationError('Date cannot be in the future.')

def validate_peak_day(value, year, month):
    """Validate that peak day is within the specified month."""
    if value:
        if value.year != year or value.month != month:
            raise ValidationError('Peak day must be within the specified month.') 