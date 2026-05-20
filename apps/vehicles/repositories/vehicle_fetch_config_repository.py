from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.vehicles.models import VehicleChallanFetchConfig
from common.constants.enums import ChallanFetchSource
from common.database.base_repository import BaseRepository


class VehicleFetchConfigRepository(BaseRepository):
    """Global fetch cooldown per vehicle_number + source (never per user)."""

    def get(self, vehicle_number: str, source: str = ChallanFetchSource.CHALLANPAY) -> VehicleChallanFetchConfig | None:
        return VehicleChallanFetchConfig.objects.filter(
            vehicle_number=vehicle_number,
            source=source,
        ).first()

    def is_cache_valid(self, config: VehicleChallanFetchConfig | None) -> bool:
        if not config or not config.last_success_fetch_at:
            return False
        ttl = timedelta(days=int(settings.CHALLAN_FETCH_CACHE_DAYS))
        return timezone.now() - config.last_success_fetch_at < ttl

    def record_success(
        self,
        vehicle_number: str,
        *,
        challan_count: int,
        source: str = ChallanFetchSource.CHALLANPAY,
    ) -> VehicleChallanFetchConfig:
        now = timezone.now()
        config, _ = VehicleChallanFetchConfig.objects.update_or_create(
            vehicle_number=vehicle_number,
            source=source,
            defaults={
                "last_success_fetch_at": now,
                "last_fetch_challan_count": challan_count,
            },
        )
        return config
