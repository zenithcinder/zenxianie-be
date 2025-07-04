from django.test import TestCase
from django.contrib.auth import get_user_model
from app.api.parking_lots.models import ParkingLot
from app.api.reports.models import DailyReport, MonthlyReport, ParkingLotReport
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from app.test.factories import (
    ParkingLotUserOwnedFactory,
    DailyReportFactory,
    MonthlyReportFactory,
    ParkingLotReportFactory
)
from django.db import IntegrityError

User = get_user_model()

class DailyReportModelTests(TestCase):
    def setUp(self):
        self.parking_lot = ParkingLotUserOwnedFactory()
        self.date = timezone.now().date()
        self.daily_report = DailyReportFactory(
            date=self.date
        )

    def test_daily_report_creation(self):
        """Test daily report creation"""
        self.assertEqual(self.daily_report.date, self.date)
        self.assertIsInstance(self.daily_report.total_revenue, Decimal)
        self.assertGreaterEqual(self.daily_report.total_revenue, 0)
        self.assertIsInstance(self.daily_report.total_reservations, int)
        self.assertGreaterEqual(self.daily_report.total_reservations, 0)
        self.assertIsInstance(self.daily_report.average_duration, float)
        self.assertGreaterEqual(self.daily_report.average_duration, 0)
        self.assertIsInstance(self.daily_report.occupancy_rate, float)
        self.assertGreaterEqual(self.daily_report.occupancy_rate, 0)
        self.assertLessEqual(self.daily_report.occupancy_rate, 100)
        self.assertIsNotNone(self.daily_report.created_at)
        self.assertIsNotNone(self.daily_report.updated_at)

    def test_daily_report_str(self):
        """Test daily report string representation"""
        expected_str = f'Daily Report - {self.date}'
        self.assertEqual(str(self.daily_report), expected_str)

    def test_daily_report_update(self):
        """Test daily report update"""
        new_revenue = Decimal('1500.00')
        new_reservations = 75
        self.daily_report.total_revenue = new_revenue
        self.daily_report.total_reservations = new_reservations
        self.daily_report.save()

        updated_report = DailyReport.objects.get(id=self.daily_report.id)
        self.assertEqual(updated_report.total_revenue, new_revenue)
        self.assertEqual(updated_report.total_reservations, new_reservations)

    def test_daily_report_delete(self):
        """Test daily report deletion"""
        report_id = self.daily_report.id
        self.daily_report.delete()
        self.assertFalse(DailyReport.objects.filter(id=report_id).exists())

    def test_daily_report_unique_date(self):
        """Test that daily report date must be unique"""
        with self.assertRaises(IntegrityError):
            DailyReportFactory(date=self.date)

class MonthlyReportModelTests(TestCase):
    def setUp(self):
        self.year = timezone.now().year
        self.month = timezone.now().month
        self.monthly_report = MonthlyReportFactory(
            year=self.year,
            month=self.month
        )

    def test_monthly_report_creation(self):
        """Test monthly report creation"""
        self.assertEqual(self.monthly_report.year, self.year)
        self.assertEqual(self.monthly_report.month, self.month)
        self.assertIsInstance(self.monthly_report.total_revenue, Decimal)
        self.assertGreaterEqual(self.monthly_report.total_revenue, 0)
        self.assertIsInstance(self.monthly_report.total_reservations, int)
        self.assertGreaterEqual(self.monthly_report.total_reservations, 0)
        self.assertIsInstance(self.monthly_report.average_duration, float)
        self.assertGreaterEqual(self.monthly_report.average_duration, 0)
        self.assertIsInstance(self.monthly_report.average_occupancy_rate, float)
        self.assertGreaterEqual(self.monthly_report.average_occupancy_rate, 0)
        self.assertLessEqual(self.monthly_report.average_occupancy_rate, 100)
        self.assertIsNotNone(self.monthly_report.created_at)
        self.assertIsNotNone(self.monthly_report.updated_at)

    def test_monthly_report_str(self):
        """Test monthly report string representation"""
        expected_str = f'Monthly Report - {self.year}/{self.month}'
        self.assertEqual(str(self.monthly_report), expected_str)

    def test_monthly_report_update(self):
        """Test monthly report update"""
        new_revenue = Decimal('35000.00')
        new_reservations = 1750
        self.monthly_report.total_revenue = new_revenue
        self.monthly_report.total_reservations = new_reservations
        self.monthly_report.save()

        updated_report = MonthlyReport.objects.get(id=self.monthly_report.id)
        self.assertEqual(updated_report.total_revenue, new_revenue)
        self.assertEqual(updated_report.total_reservations, new_reservations)

    def test_monthly_report_delete(self):
        """Test monthly report deletion"""
        report_id = self.monthly_report.id
        self.monthly_report.delete()
        self.assertFalse(MonthlyReport.objects.filter(id=report_id).exists())

    def test_monthly_report_unique_year_month(self):
        """Test that monthly report year and month combination must be unique"""
        with self.assertRaises(IntegrityError):
            MonthlyReportFactory(year=self.year, month=self.month)

class ParkingLotReportModelTests(TestCase):
    def setUp(self):
        self.parking_lot = ParkingLotUserOwnedFactory()
        self.date = timezone.now().date()
        self.parking_lot_report = ParkingLotReportFactory(
            parking_lot=self.parking_lot,
            date=self.date
        )

    def test_parking_lot_report_creation(self):
        """Test parking lot report creation"""
        self.assertEqual(self.parking_lot_report.parking_lot, self.parking_lot)
        self.assertEqual(self.parking_lot_report.date, self.date)
        self.assertIsInstance(self.parking_lot_report.total_revenue, Decimal)
        self.assertGreaterEqual(self.parking_lot_report.total_revenue, 0)
        self.assertIsInstance(self.parking_lot_report.total_reservations, int)
        self.assertGreaterEqual(self.parking_lot_report.total_reservations, 0)
        self.assertIsInstance(self.parking_lot_report.average_duration, float)
        self.assertGreaterEqual(self.parking_lot_report.average_duration, 0)
        self.assertIsInstance(self.parking_lot_report.occupancy_rate, float)
        self.assertGreaterEqual(self.parking_lot_report.occupancy_rate, 0)
        self.assertLessEqual(self.parking_lot_report.occupancy_rate, 100)
        self.assertIsNotNone(self.parking_lot_report.created_at)
        self.assertIsNotNone(self.parking_lot_report.updated_at)

    def test_parking_lot_report_str(self):
        """Test parking lot report string representation"""
        expected_str = f'{self.parking_lot.name} - {self.date}'
        self.assertEqual(str(self.parking_lot_report), expected_str)

    def test_parking_lot_report_update(self):
        """Test parking lot report update"""
        new_revenue = Decimal('1500.00')
        new_reservations = 75
        self.parking_lot_report.total_revenue = new_revenue
        self.parking_lot_report.total_reservations = new_reservations
        self.parking_lot_report.save()

        updated_report = ParkingLotReport.objects.get(id=self.parking_lot_report.id)
        self.assertEqual(updated_report.total_revenue, new_revenue)
        self.assertEqual(updated_report.total_reservations, new_reservations)

    def test_parking_lot_report_delete(self):
        """Test parking lot report deletion"""
        report_id = self.parking_lot_report.id
        self.parking_lot_report.delete()
        self.assertFalse(ParkingLotReport.objects.filter(id=report_id).exists())

    def test_parking_lot_relationship(self):
        """Test parking lot relationship"""
        # Test that report is deleted when parking lot is deleted
        parking_lot_id = self.parking_lot.id
        self.parking_lot.delete()
        
        with self.assertRaises(ParkingLotReport.DoesNotExist):
            ParkingLotReport.objects.get(id=self.parking_lot_report.id)

    def test_parking_lot_report_unique_parking_lot_date(self):
        """Test that parking lot report parking lot and date combination must be unique"""
        with self.assertRaises(IntegrityError):
            ParkingLotReportFactory(
                parking_lot=self.parking_lot,
                date=self.date
            )

    def test_generate_report_empty_data(self):
        """Test generating report with no reservations"""
        test_date = timezone.now().date() + timedelta(days=1)  # Use future date
        report = ParkingLotReport.generate_report(
            parking_lot=self.parking_lot,
            date=test_date
        )
        
        self.assertEqual(report.parking_lot, self.parking_lot)
        self.assertEqual(report.date, test_date)
        self.assertEqual(report.total_revenue, Decimal('0.00'))
        self.assertEqual(report.total_reservations, 0)
        self.assertEqual(report.occupancy_rate, 0)
        self.assertEqual(report.average_duration, 0)
        self.assertIsNone(report.peak_hour) 