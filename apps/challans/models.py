import uuid

from django.conf import settings
from django.db import models

from apps.core.models.base import TimeStampedModel
from common.constants.enums import (
    ChallanStatus,
    FetchRequestStatus,
    PaymentStatus,
    SettlementStatus,
)


class ChallanFetchRequest(TimeStampedModel):
    """Audit log for every external API fetch."""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle = models.ForeignKey("vehicles.Vehicle", on_delete=models.CASCADE, null=True)
    vehicle_number = models.CharField(max_length=12, db_index=True)
    status = models.CharField(max_length=20, choices=FetchRequestStatus.choices, default=FetchRequestStatus.PENDING)
    api_request_payload = models.JSONField(default=dict)
    raw_api_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        db_table = "challan_fetch_requests"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["vehicle_number", "created_at"]),
            models.Index(fields=["status"]),
        ]


class ChallanDetail(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challans")
    vehicle = models.ForeignKey("vehicles.Vehicle", on_delete=models.SET_NULL, null=True, related_name="challans")
    fetch_request = models.ForeignKey(ChallanFetchRequest, on_delete=models.SET_NULL, null=True, blank=True)

    challan_number = models.CharField(max_length=64, db_index=True)
    vehicle_number = models.CharField(max_length=12, db_index=True)
    chassis_number = models.CharField(max_length=64, blank=True)
    engine_number = models.CharField(max_length=64, blank=True)

    challan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    challan_status = models.CharField(max_length=32, choices=ChallanStatus.choices, default=ChallanStatus.PENDING)
    challan_type = models.CharField(max_length=64, blank=True)
    issue_date = models.DateField(null=True, blank=True)

    source_name = models.CharField(max_length=64, default="challanpay")
    source_response = models.JSONField(default=dict, blank=True)
    normalized_response = models.JSONField(default=dict, blank=True)

    payment_status = models.CharField(max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED)
    settlement_status = models.CharField(
        max_length=32, choices=SettlementStatus.choices, default=SettlementStatus.NOT_APPLICABLE
    )
    is_court_challan = models.BooleanField(default=False)

    raw_api_response = models.JSONField(default=dict, blank=True)
    api_request_payload = models.JSONField(default=dict, blank=True)

    state_name = models.CharField(max_length=64, blank=True)
    city_name = models.CharField(max_length=64, blank=True)
    offence_details = models.JSONField(default=list, blank=True)

    fetched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "challan_details"
        constraints = [
            models.UniqueConstraint(
                fields=["challan_number", "source_name"],
                name="uniq_challan_number_source",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "vehicle_number"]),
            models.Index(fields=["challan_number"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["fetched_at"]),
        ]
