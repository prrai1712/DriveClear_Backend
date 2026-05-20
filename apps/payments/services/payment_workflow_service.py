"""
Synchronous post-payment workflow (replaces Celery tasks).
Runs in-request or via on_commit for fast API response.
"""
import logging

from apps.notifications.services.notification_service import NotificationService
from apps.orders.repositories.order_repository import OrderRepository
from common.constants.enums import OrderStatus, OrderType, SettlementStatus
from common.database.db_manager import get_db_manager

logger = logging.getLogger("driveclear.payments")


class PaymentWorkflowService:
    def __init__(self, order_repo: OrderRepository | None = None):
        self._db = get_db_manager()
        self._order_repo = order_repo or OrderRepository()

    def process_after_successful_payment(self, order_id: int) -> None:
        """Advance order state after Razorpay capture — synchronous, idempotent-friendly."""
        from apps.orders.models import Order

        order = Order.objects.filter(id=order_id).select_related("user", "challan").first()
        if not order:
            return

        if order.order_status in (OrderStatus.COMPLETED, OrderStatus.SETTLEMENT_IN_PROGRESS):
            return

        def _advance():
            self._order_repo.add_timeline(order.id, "VERIFICATION_STARTED", "Challan verification started")

            if order.order_type == OrderType.COURT_SETTLEMENT:
                order.settlement_status = SettlementStatus.IN_PROGRESS
                order.order_status = OrderStatus.SETTLEMENT_IN_PROGRESS
                order.save(update_fields=["settlement_status", "order_status", "updated_at"])
                self._order_repo.add_timeline(
                    order.id, OrderStatus.SETTLEMENT_IN_PROGRESS, "Court settlement in progress"
                )
            else:
                order.order_status = OrderStatus.COMPLETED
                order.settlement_status = SettlementStatus.COMPLETED
                order.save(update_fields=["order_status", "settlement_status", "updated_at"])
                self._order_repo.add_timeline(order.id, OrderStatus.COMPLETED, "Order completed")

            self._order_repo.add_timeline(order.id, "RECEIPT_GENERATED", "Receipt available for download")
            NotificationService().notify_order_update(order)

        self._db.run_in_transaction(_advance)
        logger.info("Post-payment workflow completed", extra={"extra_data": {"order_id": order_id}})
