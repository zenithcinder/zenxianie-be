from django.shortcuts import render
from rest_framework import  permissions, status,generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import ParkingLot, ParkingSpace
from .serializers import ParkingLotSerializer, ParkingLotCreateSerializer, ParkingLotUpdateSerializer, ParkingSpaceSerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from decimal import Decimal

class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class for consistent page sizes."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ParkingLotListView(generics.ListAPIView):
    """View for listing all parking lots."""
    
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter parking lots by status if provided."""
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
    
class ParkingLotViewSet(viewsets.ModelViewSet):
    """ViewSet for managing parking lots."""
    
    queryset = ParkingLot.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ParkingLotCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ParkingLotUpdateSerializer
        return ParkingLotSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'available_spaces', 'occupancy_rate', 'search']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        """Filter parking lots based on query parameters."""
        queryset = ParkingLot.objects.all()
        
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by available spaces
        min_spaces = self.request.query_params.get('min_spaces')
        if min_spaces:
            try:
                min_spaces = int(min_spaces)
                queryset = queryset.filter(available_spaces__gte=min_spaces)
            except ValueError:
                pass
                
        # Filter by hourly rate range
        min_rate = self.request.query_params.get('min_rate')
        max_rate = self.request.query_params.get('max_rate')
        
        if min_rate:
            try:
                min_rate = Decimal(min_rate)
                queryset = queryset.filter(hourly_rate__gte=min_rate)
            except (ValueError, TypeError):
                pass
                
        if max_rate:
            try:
                max_rate = Decimal(max_rate)
                queryset = queryset.filter(hourly_rate__lte=max_rate)
            except (ValueError, TypeError):
                pass
                
        # Filter by occupancy rate
        max_occupancy = self.request.query_params.get('max_occupancy')
        if max_occupancy:
            try:
                max_occupancy = float(max_occupancy)
                queryset = [lot for lot in queryset if lot.occupancy_rate <= max_occupancy]
            except ValueError:
                pass
                
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(address__icontains=search)
            )
            
        # Sorting
        sort_by = self.request.query_params.get('sort_by', '-created_at')
        if sort_by:
            # Validate sort fields to prevent SQL injection
            allowed_sort_fields = {
                'name', '-name',
                'created_at', '-created_at',
                'available_spaces', '-available_spaces',
                'hourly_rate', '-hourly_rate',
                'status', '-status'
            }
            if sort_by in allowed_sort_fields:
                queryset = queryset.order_by(sort_by)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def available_spaces(self, request, pk=None):
        """Get available spaces in a parking lot."""
        parking_lot = self.get_object()
        available_spaces = parking_lot.spaces.filter(
            status=ParkingSpace.Status.AVAILABLE
        )
        serializer = ParkingSpaceSerializer(available_spaces, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def occupancy_rate(self, request, pk=None):
        """Get the occupancy rate of a parking lot."""
        parking_lot = self.get_object()
        return Response({
            'occupancy_rate': parking_lot.occupancy_rate,
            'total_spaces': parking_lot.total_spaces,
            'available_spaces': parking_lot.available_spaces,
            'occupied_spaces': parking_lot.total_spaces - parking_lot.available_spaces
        })
        
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search parking lots by name or address."""
        search_query = request.query_params.get('q', '')
        if not search_query:
            return Response(
                {'detail': 'Search query parameter "q" is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        parking_lots = self.get_queryset().filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query)
        )
        serializer = self.get_serializer(parking_lots, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active parking lots."""
        parking_lots = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(parking_lots, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def with_available_spaces(self, request):
        """Get parking lots with available spaces."""
        min_spaces = request.query_params.get('min_spaces', 1)
        try:
            min_spaces = int(min_spaces)
            parking_lots = self.get_queryset().filter(
                status='active',
                available_spaces__gte=min_spaces
            )
            serializer = self.get_serializer(parking_lots, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'detail': 'Invalid min_spaces parameter.'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ParkingSpaceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing parking spaces."""
    
    queryset = ParkingSpace.objects.all()
    serializer_class = ParkingSpaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'reserve', 'occupy', 'vacate']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        """Filter spaces by parking lot if lot_id is provided."""
        queryset = ParkingSpace.objects.all()
        lot_id = self.request.query_params.get('lot_id')
        if lot_id:
            queryset = queryset.filter(parking_lot_id=lot_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def reserve(self, request, pk=None):
        """Reserve a parking space."""
        space = self.get_object()
        
        if space.status != ParkingSpace.Status.AVAILABLE:
            return Response(
                {'detail': 'This space is not available for reservation.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        space.status = ParkingSpace.Status.RESERVED
        space.current_user = request.user
        space.save()
        
        return Response(
            {'detail': 'Space reserved successfully.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def occupy(self, request, pk=None):
        """Mark a space as occupied."""
        space = self.get_object()
        
        if space.status not in [ParkingSpace.Status.AVAILABLE, ParkingSpace.Status.RESERVED]:
            return Response(
                {'detail': 'This space cannot be occupied.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        space.status = ParkingSpace.Status.OCCUPIED
        space.current_user = request.user
        space.save()
        
        # Update parking lot available spaces
        parking_lot = space.parking_lot
        parking_lot.available_spaces = max(0, parking_lot.available_spaces - 1)
        parking_lot.save()
        
        return Response(
            {'detail': 'Space marked as occupied.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def vacate(self, request, pk=None):
        """Mark a space as available."""
        space = self.get_object()
        
        if space.status != ParkingSpace.Status.OCCUPIED:
            return Response(
                {'detail': 'This space is not occupied.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        space.status = ParkingSpace.Status.AVAILABLE
        space.current_user = None
        space.save()
        
        # Update parking lot available spaces
        parking_lot = space.parking_lot
        parking_lot.available_spaces = min(
            parking_lot.total_spaces,
            parking_lot.available_spaces + 1
        )
        parking_lot.save()
        
        return Response(
            {'detail': 'Space marked as available.'},
            status=status.HTTP_200_OK
        )
