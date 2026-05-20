from django.conf import settings
from django.db import models

from apps.core.models.base import TimeStampedModel


class DeviceSession(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_sessions")
    device_id = models.CharField(max_length=128, db_index=True)
    platform = models.CharField(max_length=32, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    refresh_token_jti = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        db_table = "device_sessions"
        unique_together = [("user", "device_id")]
        indexes = [
            models.Index(fields=["user", "device_id"]),
            models.Index(fields=["last_seen_at"]),
        ]


class OTPAuditLog(TimeStampedModel):
    phone_number = models.CharField(max_length=15, db_index=True)
    event = models.CharField(max_length=32)  # sent | verified | failed | rate_limited
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "otp_audit_logs"
        indexes = [models.Index(fields=["phone_number", "created_at"])]
