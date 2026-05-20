from django.conf import settings
from django.db import models

from apps.core.models.base import TimeStampedModel
from common.constants.enums import ChallanFetchSource, VehicleType


class Vehicle(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vehicles")
    vehicle_number = models.CharField(max_length=12, db_index=True)
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.PRIVATE)

    # ChallanPay external references (from user-verification)
    external_subscriber_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    external_vehicle_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    external_metadata = models.JSONField(default=dict, blank=True)

    last_searched_at = models.DateTimeField(null=True, blank=True, db_index=True)
    search_count = models.PositiveIntegerField(default=0)
    display_label = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = "vehicles"
        unique_together = [("user", "vehicle_number")]
        indexes = [
            models.Index(fields=["vehicle_number"]),
            models.Index(fields=["user", "vehicle_number"]),
        ]


class VehicleChallanFetchConfig(TimeStampedModel):
    """Global throttle + cache metadata per vehicle for external challan sources."""

    vehicle_number = models.CharField(max_length=12, db_index=True)
    source = models.CharField(
        max_length=32,
        choices=ChallanFetchSource.choices,
        default=ChallanFetchSource.CHALLANPAY,
        db_index=True,
    )
    last_success_fetch_at = models.DateTimeField(null=True, blank=True, db_index=True)
    # Pending (payable) challan count at last successful external fetch
    last_fetch_challan_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "vehicle_challan_fetch_config"
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle_number", "source"],
                name="uniq_vehicle_fetch_config_number_source",
            ),
        ]
        indexes = [
            models.Index(fields=["source", "last_success_fetch_at"]),
        ]
