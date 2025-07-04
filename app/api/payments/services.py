from django.db import transaction
from django.utils import timezone
from .models import Payment, ParkPoints, PointsTransaction
from app.api.reservations.models import Reservation

class PaymentService:
    """Service for handling payment operations."""
    
    @staticmethod
    @transaction.atomic
    def create_payment(reservation_id: int) -> Payment:
        """Create a new payment using ParkPoints."""
        try:
            reservation = Reservation.objects.select_related('user').get(id=reservation_id)
        except Reservation.DoesNotExist:
            raise ValueError("Reservation not found")
        
        if reservation.status != Reservation.Status.PENDING_PAYMENT:
            raise ValueError("Reservation is not pending payment")
        
        if hasattr(reservation, 'payment'):
            raise ValueError("Reservation already has a payment")
        
        # Get or create user's ParkPoints
        park_points, _ = ParkPoints.objects.get_or_create(user=reservation.user)
        
        # Check if user has enough points
        if park_points.balance < reservation.total_cost:
            raise ValueError("Insufficient ParkPoints balance")
        
        # Create payment
        payment = Payment.objects.create(
            reservation=reservation,
            points_amount=reservation.total_cost,
            status=Payment.PaymentStatus.PENDING
        )
        
        try:
            # Deduct points from user's balance
            park_points.balance -= reservation.total_cost
            park_points.save()
            
            # Create points transaction
            transaction = PointsTransaction.objects.create(
                points=park_points,
                amount=reservation.total_cost,
                transaction_type=PointsTransaction.TransactionType.SPEND,
                description=f"Payment for reservation #{reservation.id}"
            )
            
            # Update payment status and link transaction
            payment.status = Payment.PaymentStatus.COMPLETED
            payment.transaction = transaction
            payment.save()
            
            # Update reservation status
            reservation.status = Reservation.Status.CONFIRMED
            reservation.save()
            
            return payment
            
        except Exception as e:
            # If anything fails, mark payment as failed
            payment.status = Payment.PaymentStatus.FAILED
            payment.error_message = str(e)
            payment.save()
            raise ValueError(f"Payment failed: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def refund_payment(payment_id: int) -> Payment:
        """Refund a payment and return points to user."""
        try:
            payment = Payment.objects.select_related(
                'reservation',
                'reservation__user',
                'transaction'
            ).get(id=payment_id)
        except Payment.DoesNotExist:
            raise ValueError("Payment not found")
        
        if payment.status != Payment.PaymentStatus.COMPLETED:
            raise ValueError("Only completed payments can be refunded")
        
        if payment.status == Payment.PaymentStatus.REFUNDED:
            raise ValueError("Payment has already been refunded")
        
        # Get user's ParkPoints
        park_points = ParkPoints.objects.get(user=payment.reservation.user)
        
        try:
            # Return points to user's balance
            park_points.balance += payment.points_amount
            park_points.save()
            
            # Create refund transaction
            refund_transaction = PointsTransaction.objects.create(
                points=park_points,
                amount=payment.points_amount,
                transaction_type=PointsTransaction.TransactionType.EARN,
                description=f"Refund for payment #{payment.id}"
            )
            
            # Update payment status
            payment.status = Payment.PaymentStatus.REFUNDED
            payment.save()
            
            # Update reservation status
            payment.reservation.status = Reservation.Status.CANCELLED
            payment.reservation.save()
            
            return payment
            
        except Exception as e:
            raise ValueError(f"Refund failed: {str(e)}")
    
    @staticmethod
    def get_user_points(user_id: int) -> ParkPoints:
        """Get user's ParkPoints balance."""
        return ParkPoints.objects.get_or_create(user_id=user_id)[0]
    
    @staticmethod
    def get_user_transactions(user_id: int, page: int = 1, page_size: int = 10):
        """Get user's points transaction history."""
        transactions = PointsTransaction.objects.filter(
            points__user_id=user_id
        ).order_by('-created_at')
        
        total_items = transactions.count()
        total_pages = (total_items + page_size - 1) // page_size
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            'transactions': transactions[start:end],
            'total_pages': total_pages,
            'total_items': total_items
        } 