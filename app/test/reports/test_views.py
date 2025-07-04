from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from app.api.reports.models import DailyReport, MonthlyReport, ParkingLotReport
from app.test.factories import (
    UserFactory,
    ParkingLotUserOwnedFactory,
    DailyReportFactory,
    MonthlyReportFactory,
    ParkingLotReportFactory
)
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
import json

class ReportViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        
        # Create test data with unique dates
        self.daily_reports = DailyReportFactory.create_batch(3)
        self.monthly_reports = MonthlyReportFactory.create_batch(3)
        self.parking_lot = ParkingLotUserOwnedFactory()
        self.parking_lot_reports = ParkingLotReportFactory.create_batch(
            3,
            parking_lot=self.parking_lot
        )

    def test_list_daily_reports(self):
        """Test listing daily reports."""
        url = reverse('report-list')
        response = self.client.get(url, {'type': 'daily'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_monthly_reports(self):
        """Test listing monthly reports."""
        url = reverse('report-list')
        response = self.client.get(url, {'type': 'monthly'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_parking_lot_reports(self):
        """Test listing parking lot reports."""
        url = reverse('report-list')
        response = self.client.get(url, {'type': 'parking_lot'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_daily_report_detail(self):
        """Test getting a single daily report."""
        report = self.daily_reports[0]
        url = reverse('report-detail', args=[report.id]) + '?type=daily'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], report.id)

    def test_get_monthly_report_detail(self):
        """Test getting a single monthly report."""
        report = self.monthly_reports[0]
        url = reverse('report-detail', args=[report.id]) + '?type=monthly'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], report.id)

    def test_get_parking_lot_report_detail(self):
        """Test getting a single parking lot report."""
        report = self.parking_lot_reports[0]
        url = reverse('report-detail', args=[report.id]) + '?type=parking_lot'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], report.id)

    def test_summary_endpoint(self):
        """Test the summary endpoint."""
        url = reverse('report-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_revenue', response.data)
        self.assertIn('daily_reservations', response.data)

    def test_monthly_endpoint(self):
        """Test the monthly endpoint."""
        url = reverse('report-monthly')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_revenue', response.data)
        self.assertIn('total_reservations', response.data)

    def test_date_range_endpoint(self):
        """Test the date range endpoint."""
        url = reverse('report-date-range')
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date()
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_revenue', response.data)
        self.assertIn('total_reservations', response.data)

    def test_parking_lot_endpoint(self):
        """Test the parking lot endpoint."""
        url = reverse('report-parking-lot', args=[self.parking_lot.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_revenue', response.data)
        self.assertIn('total_reservations', response.data)

    def test_export_endpoint(self):
        """Test the export endpoint."""
        url = reverse('report-export')
        start_date = timezone.now().date() - timedelta(days=7)
        end_date = timezone.now().date()
        response = self.client.get(url, {
            'type': 'daily',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_unauthorized_access(self):
        """Test unauthorized access to reports."""
        self.client.force_authenticate(user=None)
        url = reverse('report-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_access(self):
        """Test non-staff user access to reports."""
        non_staff_user = UserFactory(is_staff=False)
        self.client.force_authenticate(user=non_staff_user)
        url = reverse('report-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_daily_report(self):
        """Test creating a daily report."""
        initial_count = DailyReport.objects.count()
        url = reverse('report-list') + '?type=daily'
        data = {
            'date': (timezone.now().date() + timedelta(days=1)).isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DailyReport.objects.count(), initial_count + 1)

    def test_update_daily_report(self):
        url = reverse('report-detail', args=[self.daily_reports[0].id]) + '?type=daily'
        data = {
            'total_revenue': '2500.00',
            'total_reservations': 125
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.daily_reports[0].refresh_from_db()
        self.assertEqual(self.daily_reports[0].total_revenue, Decimal('2500.00'))
        self.assertEqual(self.daily_reports[0].total_reservations, 125)

    def test_create_monthly_report(self):
        """Test creating a monthly report."""
        initial_count = MonthlyReport.objects.count()
        url = reverse('report-list') + '?type=monthly'
        today = timezone.now().date()
        data = {
            'year': today.year,
            'month': today.month
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MonthlyReport.objects.count(), initial_count + 1)

    def test_update_monthly_report(self):
        url = reverse('report-detail', args=[self.monthly_reports[0].id]) + '?type=monthly'
        data = {
            'total_revenue': '65000.00',
            'total_reservations': 3250
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.monthly_reports[0].refresh_from_db()
        self.assertEqual(self.monthly_reports[0].total_revenue, Decimal('65000.00'))
        self.assertEqual(self.monthly_reports[0].total_reservations, 3250)

    def test_create_parking_lot_report(self):
        """Test creating a parking lot report."""
        initial_count = ParkingLotReport.objects.count()
        url = reverse('report-list') + '?type=parking_lot'
        data = {
            'parking_lot': self.parking_lot.id,
            'date': (timezone.now().date() + timedelta(days=1)).isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ParkingLotReport.objects.count(), initial_count + 1)

    def test_update_parking_lot_report(self):
        url = reverse('report-detail', args=[self.parking_lot_reports[0].id]) + '?type=parking_lot'
        data = {
            'total_revenue': '12000.00',
            'total_reservations': 600
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parking_lot_reports[0].refresh_from_db()
        self.assertEqual(self.parking_lot_reports[0].total_revenue, Decimal('12000.00'))
        self.assertEqual(self.parking_lot_reports[0].total_reservations, 600)

    def test_regular_user_cannot_access_reports(self):
        self.client.force_authenticate(user=UserFactory(is_staff=False))
        urls = [
            reverse('report-list') + '?type=daily',
            reverse('report-list') + '?type=monthly',
            reverse('report-list') + '?type=parking_lot'
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 