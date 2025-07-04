from django.utils import timezone
from django.db import transaction
from app.api.reservations.models import Reservation
from app.api.realtime.utils import send_notification_to_user
from datetime import timedelta

class ReservationService:
    @staticmethod
    def create_reservation(user, parking_lot, start_time, end_time, **kwargs):
        """
        Create a new reservation and send notification
        """
        with transaction.atomic():
            # Create the reservation
            reservation = Reservation.objects.create(
                user=user,
                parking_lot=parking_lot,
                start_time=start_time,
                end_time=end_time,
                **kwargs
            )
            send_notification_to_user(
                user.id,
                "New reservation created",
                {
                    "reservation_id": reservation.id,
                    "parking_lot": reservation.parking_lot.name,
                    "start_time": reservation.start_time.isoformat(),
                    "end_time": reservation.end_time.isoformat(),
                }
            )
            return reservation

    @staticmethod
    def cancel_reservation(reservation_id, user):
        """
        Cancel a reservation and send notification
        """
        with transaction.atomic():
            try:
                reservation = Reservation.objects.get(id=reservation_id, user=user)
                if reservation.status == 'cancelled':
                    raise ValueError("Reservation is already cancelled")
                if reservation.status == 'expired':
                    raise ValueError("Cannot cancel an expired reservation")
                reservation.status = 'cancelled'
                reservation.save()
                send_notification_to_user(
                    user.id,
                    "Your reservation has been cancelled",
                    {
                        "reservation_id": reservation.id,
                        "parking_lot": reservation.parking_lot.name,
                    }
                )
                return reservation
            except Reservation.DoesNotExist:
                raise ValueError("Reservation not found")

    @staticmethod
    def check_expired_reservations():
        """
        Check and update expired reservations
        """
        
        # Get all active reservations that have expired
        expired_reservations = Reservation.objects.filter(
            status='active',
            end_time__lt=timezone.now()
        )
        for reservation in expired_reservations:
            reservation.status = 'expired'
            reservation.save()
            send_notification_to_user(
                reservation.user.id,
                "Your reservation has expired",
                {
                    "reservation_id": reservation.id,
                    "parking_lot": reservation.parking_lot.name,
                }
            )

    @staticmethod
    def check_upcoming_reservations():
        """
        Check and notify about upcoming reservations
        """
        # Get all active reservations starting in the next 30 minutes
        upcoming_time = timezone.now() + timedelta(minutes=30)
        upcoming_reservations = Reservation.objects.filter(
            status='active',
            start_time__lte=upcoming_time,
            start_time__gt=timezone.now()
        )
        for reservation in upcoming_reservations:
            send_notification_to_user(
                reservation.user.id,
                "Your reservation starts in 30 minutes",
                {
                    "reservation_id": reservation.id,
                    "parking_lot": reservation.parking_lot.name,
                    "start_time": reservation.start_time.isoformat(),
                }
            )

    @staticmethod
    def get_user_active_reservations(user):
        """
        Get user's active reservations
        """
        return Reservation.objects.filter(
            user=user,
            status='active',
            end_time__gt=timezone.now()
        )

    @staticmethod
    def get_user_pending_reservations(user):
        """
        Get user's pending reservations
        """
        return Reservation.objects.filter(
            user=user,
            status='pending',
            start_time__gt=timezone.now()
        )

    @staticmethod
    def get_user_expired_reservations(user):
        """
        Get user's expired reservations
        """
        return Reservation.objects.filter(
            user=user,
            status='expired'
        )

    @staticmethod
    def get_user_cancelled_reservations(user):
        """
        Get user's cancelled reservations
        """
        return Reservation.objects.filter(
            user=user,
            status='cancelled'
        )

    @staticmethod
    def update_reservation_status(reservation_id, new_status, user):
        """
        Update reservation status and send appropriate notification
        """
        with transaction.atomic():
            try:
                reservation = Reservation.objects.get(id=reservation_id, user=user)
                if reservation.status == new_status:
                    return reservation
                reservation.status = new_status
                reservation.save()
                # TODO: Send notification via Django Channels
                return reservation
            except Reservation.DoesNotExist:
                raise ValueError("Reservation not found")

    @staticmethod
    def get_reservation_details(reservation_id, user):
        """
        Get detailed information about a reservation
        """
        try:
            return Reservation.objects.get(id=reservation_id, user=user)
        except Reservation.DoesNotExist:
            raise ValueError("Reservation not found") 