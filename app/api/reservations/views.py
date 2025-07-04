from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from app.api.accounts.serializers import UserSerializer
from .models import Reservation, User
from .serializers import (
    ReservationSerializer,
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
)
from .services import ReservationService
from rest_framework.decorators import action
from django.db.models import Q
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from app.api.realtime.utils import send_notification_to_user
from django.core.exceptions import PermissionDenied


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class for consistent page sizes."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# Create your views here.


class ReservationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reservations."""

    queryset = Reservation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "create":
            return ReservationCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ReservationUpdateSerializer
        return ReservationSerializer

    def get_queryset(self):
        """Filter reservations based on user role and query parameters."""
        queryset = Reservation.objects.all()

        # Regular users can only see their own reservations
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        # Filter by status if provided
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by parking lot if provided
        parking_lot = self.request.query_params.get("parking_lot")
        if parking_lot:
            queryset = queryset.filter(parking_lot=parking_lot)

        # Filter by parking space if provided
        parking_space = self.request.query_params.get("parking_space")
        if parking_space:
            queryset = queryset.filter(parking_space=parking_space)

        # Filter by vehicle plate if provided
        vehicle_plate = self.request.query_params.get("vehicle_plate")
        if vehicle_plate:
            queryset = queryset.filter(vehicle_plate__icontains=vehicle_plate)

        # Filter by date range if provided
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                queryset = queryset.filter(start_time__date__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                queryset = queryset.filter(end_time__date__lte=end_date)
            except ValueError:
                pass

        # Filter by active/completed/cancelled
        status_filter = self.request.query_params.get("status_filter")
        if status_filter:
            if status_filter == "active":
                queryset = queryset.filter(status="active")
            elif status_filter == "completed":
                queryset = queryset.filter(status="completed")
            elif status_filter == "cancelled":
                queryset = queryset.filter(status="cancelled")

        # Search functionality
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(vehicle_plate__icontains=search)
                | Q(notes__icontains=search)
                | Q(parking_lot__name__icontains=search)
                | Q(parking_space__space_number__icontains=search)
            )

        # Sorting
        sort_by = self.request.query_params.get("sort_by", "-created_at")
        if sort_by:
            # Validate sort fields to prevent SQL injection
            allowed_sort_fields = {
                "created_at",
                "-created_at",
                "start_time",
                "-start_time",
                "end_time",
                "-end_time",
                "status",
                "-status",
                "vehicle_plate",
                "-vehicle_plate",
            }
            if sort_by in allowed_sort_fields:
                queryset = queryset.order_by(sort_by)

        return queryset

    def get_object(self):
        """Get the reservation object, allowing admin to access any reservation."""
        obj = super().get_object()
        # If user is not admin, check if they own the reservation
        if not self.request.user.is_admin and obj.user != self.request.user:
            raise PermissionDenied(
                "You don't have permission to access this reservation."
            )
        return obj

    def perform_create(self, serializer):
        """Create a new reservation using the service."""
        validated_data = serializer.validated_data

        # Get the user from the validated data
        user = validated_data.get("user")

        # If user is specified and request user is not admin, raise permission error
        if user is not None and not self.request.user.is_staff:
            raise PermissionDenied(
                "Only administrators can create reservations for other users."
            )

        # If no user specified, use the authenticated user
        if user is None:
            user = self.request.user

        try:
            reservation = ReservationService.create_reservation(
                user=user,
                parking_lot=validated_data["parking_lot"],
                parking_space=validated_data["parking_space"],
                start_time=validated_data["start_time"],
                end_time=validated_data["end_time"],
                vehicle_plate=validated_data.get("vehicle_plate"),
                notes=validated_data.get("notes"),
            )
            serializer.instance = reservation
        except Exception as e:
            raise serializers.ValidationError(str(e))

    def perform_update(self, serializer):
        """Update a reservation and notify the correct user."""
        instance = self.get_object()
        # Get the user who should receive the notification (the reservation owner)
        notification_user = instance.user

        try:
            # Perform the update
            serializer.save()

            # Send notification to the reservation owner
            user_id = getattr(notification_user, "id", None)
            send_notification_to_user(
                user_id,
                f"Your reservation has been updated",
                {
                    "reservation_id": instance.id,
                    "parking_lot": instance.parking_lot.name,
                    "updated_by": (
                        self.request.user.get_full_name()
                        if self.request.user.is_admin
                        else "You"
                    ),
                    "changes": serializer.validated_data,
                },
            )
        except Exception as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete a reservation and notify the correct user."""
        # Get the user who should receive the notification (the reservation owner)
        notification_user = instance.user

        try:
            # Send notification before deleting
            user_id = getattr(notification_user, "id", None)
            send_notification_to_user(
                user_id,
                "Your reservation has been deleted",
                {
                    "reservation_id": instance.id,
                    "parking_lot": instance.parking_lot.name,
                    "deleted_by": (
                        self.request.user.get_full_name()
                        if self.request.user.is_admin
                        else "You"
                    ),
                },
            )

            # Delete the reservation
            instance.delete()
        except Exception as e:
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a reservation using the service."""
        try:
            reservation = self.get_object()

            # Get the user who should receive the notification (the reservation owner)
            notification_user = reservation.user

            # Cancel the reservation
            reservation = ReservationService.cancel_reservation(pk, request.user)
            # Send notification to the reservation owner
            user_id = getattr(notification_user, "id", None)
            send_notification_to_user(
                user_id,
                "Your reservation has been cancelled",
                {
                    "reservation_id": reservation.id,
                    "parking_lot": reservation.parking_lot.name,
                    "cancelled_by": (
                        request.user.get_full_name() if request.user.is_admin else "You"
                    ),
                },
            )

            return Response(
                {"detail": "Reservation cancelled successfully."},
                status=status.HTTP_200_OK,
            )
        except (ValueError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark a reservation as completed using the service."""
        try:
            reservation = self.get_object()

            # Get the user who should receive the notification (the reservation owner)
            notification_user = reservation.user

            # Update the reservation status
            reservation = ReservationService.update_reservation_status(
                pk, "completed", request.user
            )

            # Send notification to the reservation owner
            send_notification_to_user(
                notification_user.id,
                "Your reservation has been marked as completed",
                {
                    "reservation_id": reservation.id,
                    "parking_lot": reservation.parking_lot.name,
                    "completed_by": (
                        request.user.get_full_name() if request.user.is_admin else "You"
                    ),
                },
            )

            return Response(
                {"detail": "Reservation marked as completed."},
                status=status.HTTP_200_OK,
            )
        except (ValueError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def my_reservations(self, request):
        """Get current user's reservations."""
        reservations = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get active reservations."""
        reservations = ReservationService.get_user_active_reservations(request.user)
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get pending reservations."""
        reservations = ReservationService.get_user_pending_reservations(request.user)
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def expired(self, request):
        """Get expired reservations."""
        reservations = ReservationService.get_user_expired_reservations(request.user)
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def cancelled(self, request):
        """Get cancelled reservations."""
        reservations = ReservationService.get_user_cancelled_reservations(request.user)
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)
