from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        NEW_RESERVATION = "new_reservation", _("New Reservation")
        RESERVATION_EXPIRED = "reservation_expired", _("Reservation Expired")
        RESERVATION_CANCELLED = "reservation_cancelled", _("Reservation Cancelled")
        UPCOMING_RESERVATION = "upcoming_reservation", _("Upcoming Reservation")
        CUSTOM = "custom", _("Custom Notification")

    class NotificationStatus(models.TextChoices):
        UNREAD = "unread", _("Unread")
        READ = "read", _("Read")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(
        max_length=50, choices=NotificationType.choices, default=NotificationType.CUSTOM
    )
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.UNREAD,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.type} - {self.user.email} - {self.created_at}"

    def mark_as_read(self):
        self.status = self.NotificationStatus.READ
        self.save(update_fields=["status", "updated_at"])
