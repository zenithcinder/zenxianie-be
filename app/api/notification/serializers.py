from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "message",
            "data",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "type", "message", "data", "created_at", "updated_at"]
