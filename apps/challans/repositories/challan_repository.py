from decimal import Decimal

from django.utils import timezone

from apps.challans.models import ChallanDetail, ChallanFetchRequest
from common.constants.enums import ChallanStatus, FetchRequestStatus, PaymentStatus
from common.database.base_repository import BaseRepository


class ChallanRepository(BaseRepository):
    def create_fetch_request(self, **kwargs) -> ChallanFetchRequest:
        return ChallanFetchRequest.objects.create(**kwargs)

    def complete_fetch_request(
        self,
        fetch_request: ChallanFetchRequest,
        status: str,
        raw: dict,
        error: str = "",
        duration_ms: int | None = None,
    ) -> ChallanFetchRequest:
        fetch_request.status = status
        fetch_request.raw_api_response = raw
        fetch_request.error_message = error
        fetch_request.duration_ms = duration_ms
        fetch_request.save(
            update_fields=["status", "raw_api_response", "error_message", "duration_ms", "updated_at"]
        )
        return fetch_request

    def upsert_challans(
        self,
        user_id: int,
        vehicle_id: int | None,
        fetch_request_id: int,
        normalized_list: list[dict],
        raw_response: dict,
        request_payload: dict,
        *,
        chassis_number: str = "",
        engine_number: str = "",
    ) -> list[ChallanDetail]:
        """Must be called inside db.atomic() from service layer."""
        results = []
        now = timezone.now()
        for item in normalized_list:
            challan_number = item.get("challan_number") or f"UNKNOWN-{item.get('vehicle_number')}"
            vehicle_number = item["vehicle_number"]
            source_name = (item.get("source") or "challanpay")[:64]
            amount = Decimal(item.get("amount") or "0")
            issue_date = item.get("issue_date") or None
            if issue_date == "":
                issue_date = None

            incoming_status = (item.get("status") or "PENDING").upper()[:32]
            existing = ChallanDetail.objects.filter(
                challan_number=challan_number,
                source_name=source_name,
            ).first()
            if existing and existing.challan_status == ChallanStatus.OPS_PENDING:
                if incoming_status not in ("PAID", "DISPOSED", "SETTLED", "CLOSED"):
                    incoming_status = ChallanStatus.OPS_PENDING

            obj, _ = ChallanDetail.objects.update_or_create(
                challan_number=challan_number,
                source_name=source_name,
                defaults={
                    "user_id": user_id,
                    "vehicle_id": vehicle_id,
                    "vehicle_number": vehicle_number,
                    "chassis_number": chassis_number,
                    "engine_number": engine_number,
                    "fetch_request_id": fetch_request_id,
                    "challan_amount": amount,
                    "penalty_amount": Decimal("0"),
                    "total_amount": amount,
                    "challan_status": incoming_status,
                    "issue_date": issue_date,
                    "state_name": item.get("state", "")[:64],
                    "city_name": (item.get("city_name") or "")[:64],
                    "offence_details": item.get("offences", []),
                    "normalized_response": item,
                    "source_response": item.get("_raw", {}),
                    "raw_api_response": raw_response,
                    "api_request_payload": request_payload,
                    "fetched_at": now,
                    "is_court_challan": bool(item.get("is_court_challan")),
                },
            )
            results.append(obj)
        return results

    def list_for_vehicle(self, vehicle_number: str, source_name: str = "challanpay"):
        """Shared challan cache for a vehicle (vehicle_number + source only — no user_id)."""
        return ChallanDetail.objects.filter(
            vehicle_number=vehicle_number,
            source_name=source_name,
        ).order_by("-fetched_at")

    def get_by_uuid(self, challan_uuid: str) -> ChallanDetail | None:
        return ChallanDetail.objects.filter(uuid=challan_uuid).first()

    def mark_ops_pending_after_payment(self, challan: ChallanDetail, *, razorpay_payment_id: str = "") -> ChallanDetail:
        challan.challan_status = ChallanStatus.OPS_PENDING
        challan.payment_status = PaymentStatus.SUCCESS
        challan.save(update_fields=["challan_status", "payment_status", "updated_at"])
        return challan

    def get_fetch_request_by_id(self, fetch_request_id: int) -> ChallanFetchRequest | None:
        return ChallanFetchRequest.objects.select_related("user", "vehicle").filter(id=fetch_request_id).first()
