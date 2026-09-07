from django.utils import timezone
from apps.core.models import NotificationRecord


class NotificationService:
    def list(self, user, unread_only: bool = False):
        queryset = NotificationRecord.objects.filter(user=user).order_by("-created_at")
        if unread_only:
            queryset = queryset.exclude(status="read")
        return queryset

    def mark_read(self, notification: NotificationRecord):
        notification.status = "read"
        notification.read_at = timezone.now()
        notification.save(update_fields=["status", "read_at"])
        return notification

    def dispatch(self, user, title: str, message: str, channel: str = "app"):
        return NotificationRecord.objects.create(
            user=user,
            title=title,
            message=message,
            channel=channel,
            status="queued",
        )
