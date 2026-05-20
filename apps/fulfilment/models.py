import uuid

from django.conf import settings
from django.db import models

from apps.core.models.base import TimeStampedModel
from apps.fulfilment.constants import FK_ITEM_ID, FK_ORDER_ID
from common.constants.enums import FulfilmentStatus, OrderType, RefundStatus


class ChallanFulfilment(TimeStampedModel):
    """
    Post-payment fulfilment queue — one row per paid challan (order line item).
    Link keys: order_id (FK to Order), item_id (FK to ChallanDetail).
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challan_fulfilments",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="fulfilments",
        db_column=FK_ORDER_ID,
    )
    challan = models.ForeignKey(
        "challans.ChallanDetail",
        on_delete=models.PROTECT,
        related_name="fulfilments",
        db_column=FK_ITEM_ID,
    )

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fulfilments",
    )
    vehicle_number = models.CharField(max_length=12, db_index=True)
    challan_number = models.CharField(max_length=64, db_index=True)

    order_type = models.CharField(max_length=32, choices=OrderType.choices)
    challan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2)

    fulfilment_status = models.CharField(
        max_length=32,
        choices=FulfilmentStatus.choices,
        default=FulfilmentStatus.PENDING,
        db_index=True,
    )

    refund_status = models.CharField(
        max_length=32,
        choices=RefundStatus.choices,
        default=RefundStatus.NONE,
        db_index=True,
    )
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    refund_reason = models.TextField(blank=True)
    razorpay_refund_id = models.CharField(max_length=64, blank=True, db_index=True)
    refund_initiated_at = models.DateTimeField(null=True, blank=True)
    refund_completed_at = models.DateTimeField(null=True, blank=True)

    razorpay_order_id = models.CharField(max_length=64, blank=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=64, blank=True, db_index=True)
    checkout_batch_id = models.UUIDField(null=True, blank=True, db_index=True)

    settlement_reference = models.CharField(max_length=128, blank=True)
    failure_reason = models.TextField(blank=True)
    ops_notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)

    class Meta:
        db_table = "challan_fulfilment"
        indexes = [
            models.Index(fields=["user", "fulfilment_status"]),
            models.Index(fields=["vehicle_number", "created_at"]),
            models.Index(fields=["challan_number"]),
            models.Index(fields=["checkout_batch_id"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=[FK_ORDER_ID], name="uniq_fulfilment_per_order"),
        ]

    def __str__(self) -> str:
        return f"{self.challan_number} ({self.fulfilment_status})"
