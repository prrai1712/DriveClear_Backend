from django.db import models

from apps.core.models.base import TimeStampedModel
from common.constants.enums import PaymentStatus, RefundStatus


class Payment(TimeStampedModel):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    payment_gateway = models.CharField(max_length=32, default="razorpay")
    gateway_order_id = models.CharField(max_length=64, db_index=True)
    gateway_payment_id = models.CharField(max_length=64, blank=True, db_index=True)
    gateway_signature = models.CharField(max_length=256, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="INR")
    payment_status = models.CharField(max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED)
    gateway_response = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refund_status = models.CharField(max_length=32, choices=RefundStatus.choices, default=RefundStatus.NONE)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["gateway_payment_id"]),
            models.Index(fields=["payment_status"]),
        ]


class PaymentWebhookLog(TimeStampedModel):
    event_type = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict)
    signature = models.CharField(max_length=256, blank=True)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "payment_webhook_logs"
        indexes = [models.Index(fields=["event_type", "created_at"])]
