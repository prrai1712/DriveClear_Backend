from django.conf import settings
from django.db import models

from apps.core.models.base import TimeStampedModel


class NotificationLog(TimeStampedModel):
    """Audit trail for outbound notifications (SMS / push)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    channel = models.CharField(max_length=32)  # sms | push | email
    event = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, default="queued")  # queued | sent | failed
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "notification_logs"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
        ]
