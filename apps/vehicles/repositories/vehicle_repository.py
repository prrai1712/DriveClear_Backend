from django.utils import timezone

from apps.vehicles.models import Vehicle
from common.constants.enums import VehicleType
from common.database.base_repository import BaseRepository


class VehicleRepository(BaseRepository):
    def get_or_create_for_user(
        self, user_id: int, vehicle_number: str, vehicle_type: str = VehicleType.PRIVATE
    ) -> tuple[Vehicle, bool]:
        return Vehicle.objects.get_or_create(
            user_id=user_id,
            vehicle_number=vehicle_number,
            defaults={"vehicle_type": vehicle_type},
        )

    def get_by_user_and_number(self, user_id: int, vehicle_number: str) -> Vehicle | None:
        return Vehicle.objects.filter(user_id=user_id, vehicle_number=vehicle_number).first()

    def get_shared_metadata(self, vehicle_number: str) -> dict:
        """RC / maker metadata from any user who fetched this vehicle (vehicle-level cache)."""
        row = (
            Vehicle.objects.filter(vehicle_number=vehicle_number)
            .exclude(external_metadata={})
            .order_by("-updated_at")
            .first()
        )
        return dict(row.external_metadata) if row and row.external_metadata else {}

    def sync_challanpay_refs_for_vehicle(
        self,
        vehicle_number: str,
        *,
        subscriber_id: int,
        vehicle_id: int,
        metadata: dict | None = None,
    ) -> None:
        """Copy ChallanPay refs to every user row for this vehicle_number."""
        updates: dict = {
            "external_subscriber_id": subscriber_id,
            "external_vehicle_id": vehicle_id,
        }
        if metadata is not None:
            updates["external_metadata"] = metadata
        Vehicle.objects.filter(vehicle_number=vehicle_number).update(**updates)

    def update_challanpay_refs(
        self,
        vehicle: Vehicle,
        *,
        subscriber_id: int,
        vehicle_id: int,
        metadata: dict | None = None,
    ) -> Vehicle:
        self.sync_challanpay_refs_for_vehicle(
            vehicle.vehicle_number,
            subscriber_id=subscriber_id,
            vehicle_id=vehicle_id,
            metadata=metadata,
        )
        vehicle.refresh_from_db()
        return vehicle

    def touch_search(self, vehicle: Vehicle, *, display_label: str = "") -> Vehicle:
        vehicle.last_searched_at = timezone.now()
        vehicle.search_count = (vehicle.search_count or 0) + 1
        if display_label:
            vehicle.display_label = display_label[:128]
        vehicle.save(update_fields=["last_searched_at", "search_count", "display_label", "updated_at"])
        return vehicle

    def list_recent_for_user(self, user_id: int, limit: int = 8):
        return (
            Vehicle.objects.filter(user_id=user_id, last_searched_at__isnull=False)
            .order_by("-last_searched_at")[:limit]
        )
