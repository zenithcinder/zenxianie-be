from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Payment, ParkPoints, PointsTransaction
from .serializers import (
    PaymentSerializer,
    CreatePaymentSerializer,
    RefundPaymentSerializer,
    ParkPointsSerializer,
    PointsTransactionSerializer
)
from .services import PaymentService

class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for handling payments."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        """Return payments for the current user."""
        return Payment.objects.filter(reservation__user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new payment using ParkPoints."""
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            payment = PaymentService.create_payment(serializer.validated_data['reservation_id'])
            return Response(self.get_serializer(payment).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Refund a payment (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admins can refund payments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RefundPaymentSerializer(data={'payment_id': pk})
        serializer.is_valid(raise_exception=True)
        
        try:
            payment = PaymentService.refund_payment(pk)
            return Response(self.get_serializer(payment).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ParkPointsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ParkPoints."""
    
    serializer_class = ParkPointsSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['add_points', 'list_all']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    def get_queryset(self):
        """Return points based on user role."""
        if self.action in ['add_points', 'list_all']:
            return ParkPoints.objects.all()
        return ParkPoints.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get points transaction history."""
        transactions = PointsTransaction.objects.filter(
            points__user=request.user
        ).order_by('-created_at')
        
        serializer = PointsTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_points(self, request, pk=None):
        """Add points to a user's balance (admin only)."""
        park_points = self.get_object()
        amount = request.data.get('amount')
        description = request.data.get('description', 'Points added by admin')
        
        if not amount or not isinstance(amount, int) or amount <= 0:
            return Response(
                {'error': 'Amount must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Add points to user's balance
            park_points.balance += amount
            park_points.save()
            
            # Create transaction record
            transaction = PointsTransaction.objects.create(
                points=park_points,
                amount=amount,
                transaction_type=PointsTransaction.TransactionType.EARN,
                description=description
            )
            
            return Response(self.get_serializer(park_points).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def list_all(self, request):
        """List all users' points (admin only)."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data) 