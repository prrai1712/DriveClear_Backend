"""
Razorpay checkout for multiple challans — one Razorpay order, many DriveClear orders.
"""
import logging
import uuid
from decimal import Decimal

import razorpay
from django.conf import settings

from apps.fulfilment.services.fulfilment_service import FulfilmentService
from apps.orders.services.order_service import OrderService
from apps.payments.repositories.payment_repository import PaymentRepository
from apps.payments.services.payment_workflow_service import PaymentWorkflowService
from common.constants.enums import OrderStatus, OrderType, PaymentStatus
from common.database.db_manager import get_db_manager
from common.database.interfaces import IDatabaseManager
from common.exceptions.base import PaymentException, ValidationException
from common.utils.idempotency import acquire_idempotency_lock, release_idempotency_lock
from common.utils.money import rupees_to_paise

logger = logging.getLogger("driveclear.payments")


class CheckoutPaymentService:
    """Industry-standard flow: create orders → single Razorpay order → verify → confirm all."""

    def __init__(self, db: IDatabaseManager | None = None):
        self._db = db or get_db_manager()
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise PaymentException(
                message="Payment gateway is not configured",
                code="PAYMENT_NOT_CONFIGURED",
            )
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        self.order_service = OrderService(self._db)
        self.order_repo = self.order_service.order_repo
        self.payment_repo = PaymentRepository(self._db)
        self.workflow = PaymentWorkflowService(self.order_repo)
        self.fulfilment_service = FulfilmentService(self._db)

    def initiate_checkout(self, user, challan_uuids: list[str], checkout_idempotency_key: str) -> dict:
        lock_key = f"checkout_init:{user.id}:{checkout_idempotency_key}"
        if not acquire_idempotency_lock(lock_key, ttl=120):
            resumed = self._try_resume_checkout(user, challan_uuids, checkout_idempotency_key)
            if resumed:
                return resumed
            raise PaymentException(message="Checkout already in progress", code="PAYMENT_DUPLICATE")

        try:
            preview = self.order_service.preview_checkout(user, challan_uuids)
            batch_id = self._resolve_checkout_batch_id(user.id, preview, checkout_idempotency_key)
            orders = self.order_service.create_orders_for_checkout(
                user,
                challan_uuids,
                batch_id,
                checkout_idempotency_key,
            )

            if not orders:
                raise ValidationException(message="No orders to pay", code="VALIDATION_ERROR")

            total = sum((o.total_amount for o in orders), Decimal("0"))
            amount_paise = rupees_to_paise(float(total))

            existing_rp_id = orders[0].razorpay_order_id if orders else ""
            batch_id = orders[0].checkout_batch_id or batch_id
            if existing_rp_id and all(o.razorpay_order_id == existing_rp_id for o in orders):
                return self._checkout_response(batch_id, orders, existing_rp_id, amount_paise, user)

            receipt = f"dc-{str(batch_id).replace('-', '')[:32]}"
            rp_order = self.client.order.create(
                {
                    "amount": amount_paise,
                    "currency": settings.CURRENCY,
                    "receipt": receipt[:40],
                    "notes": {
                        "checkout_batch_id": str(batch_id),
                        "user_id": str(user.id),
                        "challan_count": str(len(orders)),
                    },
                }
            )
            rp_order_id = rp_order["id"]

            def _persist():
                for order in orders:
                    order.razorpay_order_id = rp_order_id
                    order.checkout_batch_id = batch_id
                    order.save(update_fields=["razorpay_order_id", "checkout_batch_id", "updated_at"])
                    self.order_repo.add_timeline(
                        order.id, "PAYMENT_INITIATED", "Razorpay checkout initiated"
                    )
                    pay_key = f"pay_init:{order.id}:{rp_order_id}"
                    if not self.payment_repo.get_by_idempotency(pay_key):
                        self.payment_repo.create_payment(
                            order_id=order.id,
                            gateway_order_id=rp_order_id,
                            amount=order.total_amount,
                            payment_status=PaymentStatus.INITIATED,
                            idempotency_key=pay_key,
                        )

            self._db.run_in_transaction(_persist)
            return self._checkout_response(batch_id, orders, rp_order_id, amount_paise, user)
        except Exception:
            release_idempotency_lock(lock_key)
            raise

    def verify_checkout(
        self,
        *,
        user_id: int,
        checkout_batch_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> dict:
        if not self._verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            logger.warning(
                "Invalid Razorpay signature on checkout verify",
                extra={"extra_data": {"payment_id": razorpay_payment_id}},
            )
            raise PaymentException(message="Invalid payment signature", code="PAYMENT_FAILED")

        lock_key = f"verify:{razorpay_payment_id}"
        if not acquire_idempotency_lock(lock_key, ttl=600):
            existing = self.payment_repo.get_by_gateway_payment_id(razorpay_payment_id)
            if existing and existing.payment_status == PaymentStatus.SUCCESS:
                return self._success_payload(user_id, checkout_batch_id)
            raise PaymentException(message="Payment verification in progress", code="PAYMENT_DUPLICATE")

        orders = list(
            self.order_repo.list_by_checkout_batch(user_id, checkout_batch_id)
        )
        if not orders:
            raise PaymentException(message="Checkout batch not found", code="NOT_FOUND")

        if any(o.razorpay_order_id != razorpay_order_id for o in orders):
            raise PaymentException(message="Order mismatch with payment", code="PAYMENT_FAILED")

        if all(o.payment_status == PaymentStatus.SUCCESS for o in orders):
            for order in orders:
                self.fulfilment_service.create_from_paid_order(order)
            return self._success_payload(user_id, checkout_batch_id)

        rp_payment = self.client.payment.fetch(razorpay_payment_id)
        if rp_payment.get("status") != "captured":
            self._mark_batch_failed(orders, rp_payment)
            raise PaymentException(
                message=f"Payment not completed (status: {rp_payment.get('status')})",
                code="PAYMENT_FAILED",
            )

        expected_paise = rupees_to_paise(
            float(sum((o.total_amount for o in orders), Decimal("0")))
        )
        if int(rp_payment.get("amount", 0)) != expected_paise:
            logger.error(
                "Amount mismatch on Razorpay payment",
                extra={
                    "extra_data": {
                        "expected_paise": expected_paise,
                        "paid_paise": rp_payment.get("amount"),
                    }
                },
            )
            raise PaymentException(message="Payment amount mismatch", code="PAYMENT_FAILED")

        order_ids_for_workflow = []
        fulfilment_rows = []

        def _confirm_all():
            for order in orders:
                if order.payment_status == PaymentStatus.SUCCESS:
                    fulfilment_rows.append(self.fulfilment_service.create_from_paid_order(order))
                    continue
                payment = self.payment_repo.get_by_idempotency(
                    f"pay_init:{order.id}:{razorpay_order_id}"
                )
                if not payment:
                    raise PaymentException(message="Payment record missing", code="PAYMENT_FAILED")

                self.payment_repo.mark_success(
                    payment, razorpay_payment_id, razorpay_signature, rp_payment
                )
                self.order_repo.mark_payment_success(order, razorpay_payment_id)
                self.order_repo.add_timeline(order.id, OrderStatus.PAYMENT_SUCCESS, "Payment successful")
                next_status = (
                    OrderStatus.COURT_PROCESSING
                    if order.order_type == OrderType.COURT_SETTLEMENT
                    else OrderStatus.UNDER_REVIEW
                )
                self.order_repo.update_status(order, next_status)
                self.order_repo.add_timeline(order.id, next_status, "Order processing started")
                order_ids_for_workflow.append(order.id)
                order.refresh_from_db()
                fulfilment_rows.append(self.fulfilment_service.create_from_paid_order(order))

        self._db.run_in_transaction(_confirm_all)

        for oid in order_ids_for_workflow:
            self._db.on_commit(lambda order_id=oid: self.workflow.process_after_successful_payment(order_id))

        return self._success_payload(user_id, checkout_batch_id)

    def _success_payload(self, user_id: int, checkout_batch_id: str) -> dict:
        orders = self.order_repo.list_by_checkout_batch(user_id, checkout_batch_id)
        serialized = [
            self.order_service._serialize_order(o, include_timeline=False) for o in orders
        ]
        total = sum((o.total_amount for o in orders), Decimal("0"))
        return {
            "checkout_batch_id": str(checkout_batch_id),
            "payment_status": PaymentStatus.SUCCESS,
            "order_count": len(serialized),
            "total_paid": str(total),
            "orders": serialized,
        }

    def _mark_batch_failed(self, orders, rp_payment: dict) -> None:
        for order in orders:
            payment = self.payment_repo.get_by_idempotency(
                f"pay_init:{order.id}:{order.razorpay_order_id}"
            )
            if payment and payment.payment_status != PaymentStatus.SUCCESS:
                payment.failure_reason = f"Status: {rp_payment.get('status')}"
                payment.payment_status = PaymentStatus.FAILED
                payment.gateway_response = rp_payment
                payment.save()
            self.order_repo.add_timeline(order.id, OrderStatus.FAILED, "Payment failed")

    def _checkout_response(self, batch_id, orders, rp_order_id, amount_paise, user) -> dict:
        return {
            "checkout_batch_id": str(batch_id),
            "razorpay_order_id": rp_order_id,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount_paise": amount_paise,
            "currency": settings.CURRENCY,
            "description": f"DriveClear — {len(orders)} challan(s)",
            "order_count": len(orders),
            "order_uuids": [str(o.uuid) for o in orders],
            "prefill": {
                "name": user.name or "",
                "contact": user.phone_number or "",
            },
        }

    def _try_resume_checkout(self, user, challan_uuids: list[str], checkout_idempotency_key: str) -> dict | None:
        """If a prior attempt created orders, return checkout payload instead of 402."""
        try:
            preview = self.order_service.preview_checkout(user, challan_uuids)
            batch_id = self._resolve_checkout_batch_id(user.id, preview, checkout_idempotency_key)
            orders = self.order_service.create_orders_for_checkout(
                user, challan_uuids, batch_id, checkout_idempotency_key
            )
            if not orders:
                return None
            total = sum((o.total_amount for o in orders), Decimal("0"))
            amount_paise = rupees_to_paise(float(total))
            batch_id = orders[0].checkout_batch_id or batch_id
            existing_rp_id = orders[0].razorpay_order_id or ""
            if existing_rp_id and all(o.razorpay_order_id == existing_rp_id for o in orders):
                return self._checkout_response(batch_id, orders, existing_rp_id, amount_paise, user)
        except Exception:
            logger.exception("Failed to resume checkout after duplicate lock")
        return None

    def _resolve_checkout_batch_id(self, user_id: int, preview: dict, checkout_idempotency_key: str):
        """Reuse batch UUID when user retries checkout with the same idempotency key."""
        for item in preview["line_items"]:
            idem = f"checkout:{checkout_idempotency_key}:{item['challan_uuid']}"
            existing = self.order_repo.get_by_idempotency(idem)
            if existing and existing.checkout_batch_id:
                return existing.checkout_batch_id
        return uuid.uuid4()

    def _verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        import hashlib
        import hmac

        body = f"{order_id}|{payment_id}"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
