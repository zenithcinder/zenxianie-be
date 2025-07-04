from rest_framework import serializers
from .models import DailyReport, ParkingLotReport, MonthlyReport

class DailyReportSerializer(serializers.ModelSerializer):
    """Serializer for daily reports."""
    
    class Meta:
        model = DailyReport
        fields = [
            'id', 'date', 'total_revenue', 'total_reservations',
            'average_duration', 'peak_hour', 'occupancy_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')

class MonthlyReportSerializer(serializers.ModelSerializer):
    """Serializer for monthly reports."""
    
    class Meta:
        model = MonthlyReport
        fields = [
            'id', 'year', 'month', 'total_revenue', 'total_reservations',
            'average_duration', 'average_occupancy_rate', 'peak_day',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')

class ParkingLotReportSerializer(serializers.ModelSerializer):
    """Serializer for parking lot reports."""
    
    parking_lot_name = serializers.CharField(
        source='parking_lot.name',
        read_only=True
    )
    
    class Meta:
        model = ParkingLotReport
        fields = [
            'id', 'parking_lot', 'parking_lot_name', 'date', 'total_revenue',
            'total_reservations', 'occupancy_rate', 'average_duration',
            'peak_hour', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')

class ReportSummarySerializer(serializers.Serializer):
    """Serializer for report summary."""
    
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    daily_reservations = serializers.IntegerField()
    parking_utilization = serializers.FloatField()
    average_duration = serializers.FloatField()
    revenue_change = serializers.DecimalField(max_digits=10, decimal_places=2)
    reservation_change = serializers.IntegerField()
    utilization_change = serializers.FloatField()
    duration_change = serializers.FloatField()

class DailyReservationsSerializer(serializers.Serializer):
    """Serializer for daily reservations data."""
    
    date = serializers.DateField()
    reservations = serializers.IntegerField()

class RevenueSerializer(serializers.Serializer):
    """Serializer for revenue data."""
    
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

class PeakHoursSerializer(serializers.Serializer):
    """Serializer for peak hours data."""
    
    hour = serializers.DateTimeField()
    usage = serializers.IntegerField()

class UserDemographicsSerializer(serializers.Serializer):
    """Serializer for user demographics data."""
    
    name = serializers.CharField()
    value = serializers.IntegerField()

class DateRangeReportSerializer(serializers.Serializer):
    """Serializer for date range reports."""
    
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_reservations = serializers.IntegerField()
    average_duration = serializers.FloatField()
    average_occupancy_rate = serializers.FloatField()
    daily_data = DailyReservationsSerializer(many=True)
    revenue_data = RevenueSerializer(many=True) 