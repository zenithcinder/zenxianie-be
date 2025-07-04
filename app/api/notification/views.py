from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Notification
from .serializers import NotificationSerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class for consistent page sizes."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    Users can only read and delete their own notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    http_method_names = ['get', 'delete']  # Only allow GET and DELETE methods

    def get_queryset(self):
        """Filter notifications to only show the current user's notifications."""
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by type if provided
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(message__icontains=search) |
                Q(data__icontains=search)
            )
        
        # Sorting
        sort_by = self.request.query_params.get('sort_by', '-created_at')
        if sort_by:
            # Validate sort fields to prevent SQL injection
            allowed_sort_fields = {
                'created_at', '-created_at',
                'updated_at', '-updated_at',
                'status', '-status',
                'type', '-type'
            }
            if sort_by in allowed_sort_fields:
                queryset = queryset.order_by(sort_by)
        
        return queryset

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read."""
        self.get_queryset().update(status=Notification.NotificationStatus.READ)
        return Response({'status': 'all notifications marked as read'})

    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        """Delete all notifications."""
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = self.get_queryset().filter(
            status=Notification.NotificationStatus.UNREAD
        ).count()
        return Response({'unread_count': count}) 