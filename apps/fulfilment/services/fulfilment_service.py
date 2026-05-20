import logging

from django.utils import timezone

from apps.challans.repositories.challan_repository import ChallanRepository
from apps.fulfilment.repositories.fulfilment_repository import FulfilmentRepository
from common.constants.enums import ChallanStatus, FulfilmentStatus, PaymentStatus
from common.database.db_manager import get_db_manager
from common.database.interfaces import IDatabaseManager

logger = logging.getLogger("driveclear.fulfilment")


class FulfilmentService:
    """Creates and updates challan_fulfilment rows after payment / ops settlement."""

    def __init__(self, db: IDatabaseManager | None = None):
        self._db = db or get_db_manager()
        self.repo = FulfilmentRepository(self._db)
        self.challan_repo = ChallanRepository(self._db)

    def create_from_paid_order(self, order) -> dict:
        """
        Idempotent: one fulfilment row per order; challan → OPS_PENDING.
        """
        idem = f"fulfilment:order:{order.id}"
        existing = self.repo.get_by_idempotency(idem)
        if existing:
            return self._serialize(existing)

        challan = order.challan
        if challan.challan_status != ChallanStatus.OPS_PENDING:
            self.challan_repo.mark_ops_pending_after_payment(
                challan,
                razorpay_payment_id=order.razorpay_payment_id or "",
            )

        fulfilment = self.repo.create_fulfilment(
            user_id=order.user_id,
            order_id=order.id,
            challan_id=challan.id,
            vehicle_id=challan.vehicle_id,
            vehicle_number=challan.vehicle_number,
            challan_number=challan.challan_number,
            order_type=order.order_type,
            challan_amount=order.payable_amount,
            service_fee=order.convenience_fee,
            total_paid=order.total_amount,
            fulfilment_status=FulfilmentStatus.PENDING,
            razorpay_order_id=order.razorpay_order_id or "",
            razorpay_payment_id=order.razorpay_payment_id or "",
            checkout_batch_id=order.checkout_batch_id,
            paid_at=order.payment_completed_at or timezone.now(),
            idempotency_key=idem,
            metadata={
                "order_uuid": str(order.uuid),
                "challan_uuid": str(challan.uuid),
                "is_court_challan": challan.is_court_challan,
            },
        )
        logger.info(
            "Fulfilment created",
            extra={
                "extra_data": {
                    "fulfilment_uuid": str(fulfilment.uuid),
                    "order_id": order.id,
                    "challan_number": challan.challan_number,
                }
            },
        )
        return self._serialize(fulfilment)

    def _serialize(self, f) -> dict:
        return {
            "uuid": str(f.uuid),
            "order_id": f.order_id,
            "item_id": f.challan_id,
            "challan_number": f.challan_number,
            "vehicle_number": f.vehicle_number,
            "fulfilment_status": f.fulfilment_status,
            "refund_status": f.refund_status,
            "total_paid": str(f.total_paid),
            "paid_at": f.paid_at,
        }
