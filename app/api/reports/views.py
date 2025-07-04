from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta, datetime
import csv
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from .models import DailyReport, ParkingLotReport, MonthlyReport
from .serializers import (
    DailyReportSerializer, ParkingLotReportSerializer,
    ReportSummarySerializer, DailyReservationsSerializer,
    RevenueSerializer, PeakHoursSerializer,
    UserDemographicsSerializer, MonthlyReportSerializer,
    DateRangeReportSerializer
)
from app.api.reservations.models import Reservation
from app.api.parking_lots.models import ParkingLot

class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for generating and retrieving reports."""
    
    permission_classes = [permissions.IsAdminUser]
    queryset = DailyReport.objects.all()
    serializer_class = DailyReportSerializer
    
    def get_queryset(self):
        """Return appropriate queryset based on the report type."""
        report_type = self.request.query_params.get('type', 'daily')
        if report_type == 'monthly':
            return MonthlyReport.objects.all()
        elif report_type == 'parking_lot':
            return ParkingLotReport.objects.all()
        return DailyReport.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on the report type."""
        report_type = self.request.query_params.get('type', 'daily')
        if report_type == 'monthly':
            return MonthlyReportSerializer
        elif report_type == 'parking_lot':
            return ParkingLotReportSerializer
        return DailyReportSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new report based on the report type."""
        report_type = request.query_params.get('type', 'daily')
        
        if report_type == 'daily':
            date = request.data.get('date')
            if not date:
                return Response(
                    {'detail': 'Date is required for daily reports.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            report = DailyReport.generate_report(date=date)
            serializer = DailyReportSerializer(report)
            
        elif report_type == 'monthly':
            year = request.data.get('year')
            month = request.data.get('month')
            if not year or not month:
                return Response(
                    {'detail': 'Year and month are required for monthly reports.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                year = int(year)
                month = int(month)
            except ValueError:
                return Response(
                    {'detail': 'Year and month must be integers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            report = MonthlyReport.generate_report(year=year, month=month)
            serializer = MonthlyReportSerializer(report)
            
        elif report_type == 'parking_lot':
            parking_lot_id = request.data.get('parking_lot')
            date = request.data.get('date')
            if not parking_lot_id or not date:
                return Response(
                    {'detail': 'Parking lot ID and date are required for parking lot reports.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                parking_lot = ParkingLot.objects.get(pk=parking_lot_id)
                date = datetime.strptime(date, '%Y-%m-%d').date()
            except ParkingLot.DoesNotExist:
                return Response(
                    {'detail': 'Parking lot not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError:
                return Response(
                    {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            report = ParkingLotReport.generate_report(parking_lot=parking_lot, date=date)
            serializer = ParkingLotReportSerializer(report)
            
        else:
            return Response(
                {'detail': 'Invalid report type. Use daily, monthly, or parking_lot.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of current day's statistics."""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get today's data
        today_reservations = Reservation.objects.filter(
            start_time__date=today,
            status__in=['active', 'completed']
        )
        today_revenue = sum(r.total_cost for r in today_reservations)
        today_count = today_reservations.count()
        today_duration = sum(r.duration for r in today_reservations) / today_count if today_count > 0 else 0
        
        # Get yesterday's data for comparison
        yesterday_reservations = Reservation.objects.filter(
            start_time__date=yesterday,
            status__in=['active', 'completed']
        )
        yesterday_revenue = sum(r.total_cost for r in yesterday_reservations)
        yesterday_count = yesterday_reservations.count()
        yesterday_duration = sum(r.duration for r in yesterday_reservations) / yesterday_count if yesterday_count > 0 else 0
        
        # Calculate overall parking utilization
        total_spaces = sum(lot.total_spaces for lot in ParkingLot.objects.all())
        occupied_spaces = sum(lot.total_spaces - lot.available_spaces for lot in ParkingLot.objects.all())
        utilization = (occupied_spaces / total_spaces * 100) if total_spaces > 0 else 0
        
        # Calculate yesterday's utilization
        yesterday_utilization = DailyReport.objects.filter(date=yesterday).first()
        yesterday_utilization = yesterday_utilization.occupancy_rate if yesterday_utilization else 0
        
        data = {
            'total_revenue': today_revenue,
            'daily_reservations': today_count,
            'parking_utilization': utilization,
            'average_duration': today_duration,
            'revenue_change': today_revenue - yesterday_revenue,
            'reservation_change': today_count - yesterday_count,
            'utilization_change': utilization - yesterday_utilization,
            'duration_change': today_duration - yesterday_duration
        }
        
        serializer = ReportSummarySerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly report for the current month."""
        today = timezone.now()
        year = today.year
        month = today.month
        
        report = MonthlyReport.generate_report(year=year, month=month)
        serializer = MonthlyReportSerializer(report)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get report for a custom date range."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'detail': 'Both start_date and end_date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get reservations for the date range
        reservations = Reservation.objects.filter(
            start_time__date__range=[start_date, end_date],
            status__in=['active', 'completed']
        )
        
        # Calculate summary statistics
        total_revenue = sum(r.total_cost for r in reservations)
        total_reservations = reservations.count()
        average_duration = sum(r.duration for r in reservations) / total_reservations if total_reservations > 0 else 0
        
        # Calculate average occupancy rate
        daily_reports = DailyReport.objects.filter(
            date__range=[start_date, end_date]
        )
        average_occupancy_rate = sum(report.occupancy_rate for report in daily_reports) / len(daily_reports) if daily_reports else 0
        
        # Get daily data
        daily_data = reservations.annotate(
            date=TruncDate('start_time')
        ).values('date').annotate(
            reservations=Count('id')
        ).order_by('date')
        
        # Get revenue data by date
        revenue_data = []
        for date in daily_data:
            date_reservations = reservations.filter(start_time__date=date['date'])
            revenue = sum(r.total_cost for r in date_reservations)
            revenue_data.append({
                'date': date['date'],
                'revenue': revenue
            })
        
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': total_revenue,
            'total_reservations': total_reservations,
            'average_duration': average_duration,
            'average_occupancy_rate': average_occupancy_rate,
            'daily_data': daily_data,
            'revenue_data': revenue_data
        }
        
        serializer = DateRangeReportSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export report data to CSV."""
        report_type = request.query_params.get('type', 'daily')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'detail': 'Both start_date and end_date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{start_date}_{end_date}.csv"'
        
        writer = csv.writer(response)
        
        if report_type == 'daily':
            reports = DailyReport.objects.filter(date__range=[start_date, end_date])
            writer.writerow(['Date', 'Total Revenue', 'Total Reservations', 'Average Duration', 'Peak Hour', 'Occupancy Rate'])
            for report in reports:
                writer.writerow([
                    report.date,
                    report.total_revenue,
                    report.total_reservations,
                    report.average_duration,
                    report.peak_hour,
                    report.occupancy_rate
                ])
        elif report_type == 'monthly':
            reports = MonthlyReport.objects.filter(
                year__gte=start_date.year,
                year__lte=end_date.year,
                month__gte=start_date.month if start_date.year == end_date.year else 1,
                month__lte=end_date.month if start_date.year == end_date.year else 12
            )
            writer.writerow(['Year', 'Month', 'Total Revenue', 'Total Reservations', 'Average Duration', 'Average Occupancy Rate', 'Peak Day'])
            for report in reports:
                writer.writerow([
                    report.year,
                    report.month,
                    report.total_revenue,
                    report.total_reservations,
                    report.average_duration,
                    report.average_occupancy_rate,
                    report.peak_day
                ])
        elif report_type == 'parking_lot':
            reports = ParkingLotReport.objects.filter(date__range=[start_date, end_date])
            writer.writerow(['Parking Lot', 'Date', 'Total Revenue', 'Total Reservations', 'Occupancy Rate', 'Average Duration', 'Peak Hour'])
            for report in reports:
                writer.writerow([
                    report.parking_lot.name,
                    report.date,
                    report.total_revenue,
                    report.total_reservations,
                    report.occupancy_rate,
                    report.average_duration,
                    report.peak_hour
                ])
        else:
            return Response(
                {'detail': 'Invalid report type. Use daily, monthly, or parking_lot.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return response
    
    @action(detail=False, methods=['get'])
    def daily_reservations(self, request):
        """Get daily reservations data for the last 7 days."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=6)
        
        reservations = Reservation.objects.filter(
            start_time__date__range=[start_date, end_date],
            status__in=['active', 'completed']
        ).annotate(
            date=TruncDate('start_time')
        ).values('date').annotate(
            reservations=Count('id')
        ).order_by('date')
        
        serializer = DailyReservationsSerializer(reservations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Get revenue data for the last 7 days."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=6)
        
        # Get reservations for the date range
        reservations = Reservation.objects.filter(
            start_time__date__range=[start_date, end_date],
            status__in=['active', 'completed']
        )
        
        # Calculate revenue by date
        revenue_data = []
        for date in (start_date + timedelta(days=x) for x in range(7)):
            date_reservations = reservations.filter(start_time__date=date)
            total_revenue = sum(r.total_cost for r in date_reservations)
            revenue_data.append({
                'date': date,
                'revenue': total_revenue
            })
        
        serializer = RevenueSerializer(revenue_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def peak_hours(self, request):
        """Get peak hours data for today."""
        today = timezone.now().date()
        
        reservations = Reservation.objects.filter(
            start_time__date=today,
            status__in=['active', 'completed']
        ).annotate(
            hour=TruncHour('start_time')
        ).values('hour').annotate(
            usage=Count('id')
        ).order_by('hour')
        
        serializer = PeakHoursSerializer(reservations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_demographics(self, request):
        """Get user demographics data."""
        # Get user counts by role
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user_counts = User.objects.values('role').annotate(
            value=Count('id')
        ).values('role', 'value')
        
        # Format data for the serializer
        data = [
            {'name': role, 'value': count}
            for role, count in user_counts
        ]
        
        serializer = UserDemographicsSerializer(data, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def parking_lot(self, request, pk=None):
        """Get detailed report for a specific parking lot."""
        try:
            parking_lot = ParkingLot.objects.get(pk=pk)
        except ParkingLot.DoesNotExist:
            return Response(
                {'detail': 'Parking lot not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get date from query params or use today's date
        date_str = request.query_params.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date = timezone.now().date()
        
        # Try to get existing report first
        try:
            report = ParkingLotReport.objects.get(parking_lot=parking_lot, date=date)
        except ParkingLotReport.DoesNotExist:
            # Generate new report if it doesn't exist
            report = ParkingLotReport.generate_report(
                parking_lot=parking_lot,
                date=date
            )
        
        serializer = ParkingLotReportSerializer(report)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Get daily report for a specific date."""
        date_str = request.query_params.get('date')
        
        if not date_str:
            # If no date provided, use today's date
            date = timezone.now().date()
        else:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get or create daily report
        report = DailyReport.generate_report(date=date)
        serializer = DailyReportSerializer(report)
        return Response(serializer.data)
    
    def get_object(self):
        """Return the appropriate object based on the report type."""
        report_type = self.request.query_params.get('type', 'daily')
        pk = self.kwargs.get('pk')
        
        if report_type == 'monthly':
            return MonthlyReport.objects.get(pk=pk)
        elif report_type == 'parking_lot':
            return ParkingLotReport.objects.get(pk=pk)
        return DailyReport.objects.get(pk=pk) 