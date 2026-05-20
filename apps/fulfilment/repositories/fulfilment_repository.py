from django.utils import timezone

from apps.fulfilment.models import ChallanFulfilment
from common.constants.enums import ChallanStatus, FulfilmentStatus, PaymentStatus, RefundStatus
from common.database.base_repository import BaseRepository


class FulfilmentRepository(BaseRepository):
    def get_by_idempotency(self, key: str) -> ChallanFulfilment | None:
        return ChallanFulfilment.objects.filter(idempotency_key=key).first()

    def get_by_order_id(self, order_id: int) -> ChallanFulfilment | None:
        return ChallanFulfilment.objects.filter(order_id=order_id).select_related("challan", "order").first()

    def create_fulfilment(self, **kwargs) -> ChallanFulfilment:
        return ChallanFulfilment.objects.create(**kwargs)

    def mark_success(self, fulfilment: ChallanFulfilment, *, settlement_reference: str = "") -> ChallanFulfilment:
        now = timezone.now()
        fulfilment.fulfilment_status = FulfilmentStatus.SUCCESS
        fulfilment.fulfilled_at = now
        if settlement_reference:
            fulfilment.settlement_reference = settlement_reference
        fulfilment.save(
            update_fields=[
                "fulfilment_status",
                "fulfilled_at",
                "settlement_reference",
                "updated_at",
            ]
        )
        challan = fulfilment.challan
        challan.challan_status = ChallanStatus.PAID
        challan.payment_status = PaymentStatus.SUCCESS
        challan.save(update_fields=["challan_status", "payment_status", "updated_at"])
        return fulfilment

    def mark_failed(
        self,
        fulfilment: ChallanFulfilment,
        *,
        failure_reason: str,
        refund_status: str = RefundStatus.NONE,
    ) -> ChallanFulfilment:
        fulfilment.fulfilment_status = FulfilmentStatus.FAILED
        fulfilment.failure_reason = failure_reason[:2000]
        fulfilment.refund_status = refund_status
        fulfilment.save(
            update_fields=["fulfilment_status", "failure_reason", "refund_status", "updated_at"]
        )
        return fulfilment
