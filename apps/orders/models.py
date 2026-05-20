import uuid

from django.conf import settings
from django.db import models

from apps.core.models.base import TimeStampedModel
from common.constants.enums import (
    OrderStatus,
    OrderType,
    PaymentStatus,
    RefundStatus,
    SettlementStatus,
)


class Order(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    challan = models.ForeignKey("challans.ChallanDetail", on_delete=models.PROTECT, related_name="orders")

    order_type = models.CharField(max_length=32, choices=OrderType.choices)
    order_status = models.CharField(max_length=32, choices=OrderStatus.choices, default=OrderStatus.CREATED)
    payment_status = models.CharField(max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED)
    settlement_status = models.CharField(
        max_length=32, choices=SettlementStatus.choices, default=SettlementStatus.NOT_APPLICABLE
    )

    payable_amount = models.DecimalField(max_digits=12, decimal_places=2)  # challan amount
    convenience_fee = models.DecimalField(max_digits=12, decimal_places=2)  # ₹99 or ₹999
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    razorpay_order_id = models.CharField(max_length=64, blank=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=64, blank=True, db_index=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)

    refund_status = models.CharField(max_length=32, choices=RefundStatus.choices, default=RefundStatus.NONE)
    refund_reason = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    checkout_batch_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["user", "order_status"]),
            models.Index(fields=["razorpay_order_id"]),
            models.Index(fields=["checkout_batch_id"]),
            models.Index(fields=["created_at"]),
        ]


class OrderTimeline(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="timeline")
    status = models.CharField(max_length=64)
    message = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "order_timeline"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["order", "created_at"])]
