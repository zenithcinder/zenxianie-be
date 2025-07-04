from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'message', 'status', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('user__email', 'message')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',) 