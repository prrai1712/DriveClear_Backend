import logging
from uuid import uuid4

from django.conf import settings

from apps.challans.repositories.challan_repository import ChallanRepository
from apps.challans.services.challan_normalizer import ChallanNormalizer
from apps.challans.services.challan_pending import count_pending_normalized, count_pending_serialized
from apps.challans.services.challan_serializer import ChallanResponseSerializer
from apps.challans.services.vehicle_rc_fields import build_vehicle_metadata
from apps.challans.services.external_challan_client import ExternalChallanClient
from apps.vehicles.repositories.vehicle_fetch_config_repository import VehicleFetchConfigRepository
from apps.vehicles.repositories.vehicle_repository import VehicleRepository
from common.constants.enums import ChallanFetchSource, FetchRequestStatus, VehicleType
from common.database.db_manager import get_db_manager
from common.database.interfaces import IDatabaseManager
from common.logging.context import get_correlation_id
from common.validators.vehicle import validate_vehicle_number

logger = logging.getLogger("driveclear")


class ChallanFetchService:
    """
    Challan fetch flow (vehicle-level, not user-level):

    1. U1 searches vehicle V1 → ChallanPay → rows in challan_details + config for (V1, source).
    2. U2 searches V1 within CHALLAN_FETCH_CACHE_DAYS → read challan_details for V1 only;
       no ChallanPay call. user_id is NOT used for cache lookups.
    """

    def __init__(self, db: IDatabaseManager | None = None):
        self._db = db or get_db_manager()
        self.vehicle_repo = VehicleRepository(self._db)
        self.fetch_config_repo = VehicleFetchConfigRepository(self._db)
        self.challan_repo = ChallanRepository(self._db)
        self.client = ExternalChallanClient()
        self.normalizer = ChallanNormalizer()
        self.source = ChallanFetchSource.CHALLANPAY

    def fetch_for_vehicle(
        self,
        user,
        vehicle_number: str,
        vehicle_type: str = VehicleType.PRIVATE,
    ) -> dict:
        vehicle_number = validate_vehicle_number(vehicle_number)
        vehicle, _ = self.vehicle_repo.get_or_create_for_user(user.id, vehicle_number, vehicle_type)

        fetch_config = self.fetch_config_repo.get(vehicle_number, self.source)
        if self.fetch_config_repo.is_cache_valid(fetch_config):
            logger.info(
                "Challan fetch served from DB cache (vehicle + source)",
                extra={"vehicle_number": vehicle_number, "source": self.source},
            )
            return self._serve_from_db(vehicle, vehicle_number)

        logger.info(
            "Challan fetch calling external API",
            extra={"vehicle_number": vehicle_number, "source": self.source},
        )
        return self._fetch_from_external(user, vehicle, vehicle_number, vehicle_type)

    def _serve_from_db(self, vehicle, vehicle_number: str) -> dict:
        challans = list(self.challan_repo.list_for_vehicle(vehicle_number, source_name=self.source))
        serialized = [ChallanResponseSerializer.serialize(c) for c in challans]
        pending_count = count_pending_serialized(serialized)

        metadata = self.vehicle_repo.get_shared_metadata(vehicle_number)
        if serialized:
            if not metadata.get("chassis_number"):
                metadata["chassis_number"] = serialized[0].get("chassis_number", "")
            if not metadata.get("engine_number"):
                metadata["engine_number"] = serialized[0].get("engine_number", "")
        label = metadata.get("maker_model") or metadata.get("vehicle_category") or ""
        self.vehicle_repo.touch_search(vehicle, display_label=label)

        return self._build_response(
            vehicle=vehicle,
            vehicle_number=vehicle_number,
            metadata=metadata,
            serialized=serialized,
            from_cache=True,
            no_challans_found=pending_count == 0,
            pending_count=pending_count,
        )

    def _fetch_from_external(self, user, vehicle, vehicle_number: str, vehicle_type: str) -> dict:
        payload = {
            "name": user.name,
            "phone": user.phone_number,
            "vehicleNo": vehicle_number,
            "vehicleType": vehicle_type,
            "utmSource": settings.EXTERNAL_CHALLAN_UTM_SOURCE,
        }

        fetch_request = self.challan_repo.create_fetch_request(
            user_id=user.id,
            vehicle_id=vehicle.id,
            vehicle_number=vehicle_number,
            api_request_payload=payload,
            correlation_id=get_correlation_id(),
        )

        try:
            raw, duration_ms = self.client.fetch_challans(
                name=user.name or "User",
                phone=user.phone_number,
                vehicle_no=vehicle_number,
                vehicle_type=vehicle_type,
            )

            find_payload = raw.get("find_challans") or raw
            normalized = self.normalizer.normalize_list(find_payload, vehicle_number)

            metadata = build_vehicle_metadata(
                raw,
                subscriber_id=raw.get("subscriber_id"),
                vehicle_id=raw.get("vehicle_id"),
            )
            chassis_number = metadata["chassis_number"]
            engine_number = metadata["engine_number"]

            with self._db.atomic():
                self.vehicle_repo.update_challanpay_refs(
                    vehicle,
                    subscriber_id=int(raw["subscriber_id"]),
                    vehicle_id=int(raw["vehicle_id"]),
                    metadata=metadata,
                )
                challans = self.challan_repo.upsert_challans(
                    user_id=user.id,
                    vehicle_id=vehicle.id,
                    fetch_request_id=fetch_request.id,
                    normalized_list=normalized,
                    raw_response=raw,
                    request_payload=payload,
                    chassis_number=chassis_number,
                    engine_number=engine_number,
                )
                self.challan_repo.complete_fetch_request(
                    fetch_request,
                    FetchRequestStatus.SUCCESS,
                    raw,
                    duration_ms=duration_ms,
                )
                pending_count = count_pending_normalized(normalized)
                self.fetch_config_repo.record_success(
                    vehicle_number,
                    challan_count=pending_count,
                    source=self.source,
                )

            label = metadata.get("maker_model") or metadata.get("vehicle_category") or ""
            self.vehicle_repo.touch_search(vehicle, display_label=label)

            serialized = [ChallanResponseSerializer.serialize(c) for c in challans]
            pending_count = count_pending_serialized(serialized)
            return self._build_response(
                vehicle=vehicle,
                vehicle_number=vehicle_number,
                metadata=metadata,
                serialized=serialized,
                fetch_request_uuid=str(fetch_request.uuid),
                from_cache=False,
                no_challans_found=pending_count == 0,
                pending_count=pending_count,
            )

        except Exception as exc:
            self.challan_repo.complete_fetch_request(
                fetch_request,
                FetchRequestStatus.FAILED,
                {},
                error=str(exc),
            )
            fetch_request.retry_count += 1
            fetch_request.save(update_fields=["retry_count", "updated_at"])
            raise

    def _build_response(
        self,
        *,
        vehicle,
        vehicle_number: str,
        metadata: dict,
        serialized: list[dict],
        fetch_request_uuid: str | None = None,
        from_cache: bool = False,
        no_challans_found: bool = False,
        pending_count: int | None = None,
    ) -> dict:
        rc = metadata.get("rc") or {}
        pending = pending_count if pending_count is not None else count_pending_serialized(serialized)
        return {
            "fetch_request_id": fetch_request_uuid or str(uuid4()),
            "vehicle_number": vehicle_number,
            "vehicle": {
                "vehicle_number": vehicle.vehicle_number,
                "external_subscriber_id": vehicle.external_subscriber_id,
                "external_vehicle_id": vehicle.external_vehicle_id,
                "maker_model": metadata.get("maker_model", ""),
                "owner_name": metadata.get("owner_name") or rc.get("ownerName", ""),
                "chassis_number": metadata.get("chassis_number", ""),
                "engine_number": metadata.get("engine_number", ""),
            },
            "count": len(serialized),
            "pending_count": pending,
            "challans": serialized,
            "from_cache": from_cache,
            "no_challans_found": no_challans_found or pending == 0,
            "cache_ttl_days": int(settings.CHALLAN_FETCH_CACHE_DAYS),
        }
