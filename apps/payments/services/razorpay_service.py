import hashlib
import hmac
import json
import logging

import razorpay
from django.conf import settings

from apps.orders.repositories.order_repository import OrderRepository
from apps.orders.services.order_service import OrderService
from apps.payments.repositories.payment_repository import PaymentRepository
from apps.payments.services.payment_workflow_service import PaymentWorkflowService
from common.constants.enums import OrderStatus, OrderType, PaymentStatus
from common.database.db_manager import get_db_manager
from common.database.interfaces import IDatabaseManager
from common.exceptions.base import PaymentException
from common.utils.idempotency import acquire_idempotency_lock
from common.utils.money import rupees_to_paise

logger = logging.getLogger("driveclear.payments")


class RazorpayService:
    def __init__(self, db: IDatabaseManager | None = None):
        self._db = db or get_db_manager()
        self.mock_mode = getattr(settings, "MOCK_PAYMENTS", False) or not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET
        if not self.mock_mode:
            self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        else:
            self.client = None
            logger.info("Razorpay credentials missing or MOCK_PAYMENTS active. Using Mock payments fallback.")
        self.order_repo = OrderRepository(self._db)
        self.payment_repo = PaymentRepository(self._db)
        self.workflow = PaymentWorkflowService(self.order_repo)

    def create_razorpay_order(self, user, order_uuid: str) -> dict:
        order = self.order_repo.get_by_uuid(user.id, order_uuid)
        if not order:
            raise PaymentException(message="Order not found", code="NOT_FOUND")

        if order.razorpay_order_id:
            return self._checkout_payload(order)

        amount_paise = rupees_to_paise(float(order.total_amount))
        if self.mock_mode:
            import uuid
            rp_order_id = f"order_mock_{uuid.uuid4().hex[:20]}"
        else:
            rp_order = self.client.order.create(
                {
                    "amount": amount_paise,
                    "currency": settings.CURRENCY,
                    "receipt": str(order.uuid)[:40],
                    "notes": {
                        "driveclear_order_uuid": str(order.uuid),
                        "user_id": str(user.id),
                    },
                }
            )
            rp_order_id = rp_order["id"]

        def _persist():
            order.razorpay_order_id = rp_order_id
            order.save(update_fields=["razorpay_order_id", "updated_at"])
            self.order_repo.add_timeline(
                order.id,
                "PAYMENT_INITIATED",
                "Payment initiated with Razorpay (Mock)" if self.mock_mode else "Payment initiated with Razorpay"
            )
            self.payment_repo.create_payment(
                order_id=order.id,
                gateway_order_id=rp_order_id,
                amount=order.total_amount,
                payment_status=PaymentStatus.INITIATED,
                idempotency_key=f"pay_init:{order.id}:{rp_order_id}",
            )

        self._db.run_in_transaction(_persist)
        return self._checkout_payload(order)

    def verify_payment(
        self,
        *,
        order_uuid: str,
        user_id: int,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> dict:
        lock_key = f"verify:{razorpay_payment_id}"
        if not acquire_idempotency_lock(lock_key, ttl=600):
            existing = self.payment_repo.get_by_gateway_payment_id(razorpay_payment_id)
            if existing and existing.payment_status == PaymentStatus.SUCCESS:
                order = self.order_repo.get_by_uuid(user_id, order_uuid)
                return OrderService(self._db)._serialize_order(order, include_timeline=True)
            raise PaymentException(message="Payment verification in progress", code="PAYMENT_DUPLICATE")

        if not self.mock_mode:
            if not self._verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
                logger.warning("Invalid Razorpay signature", extra={"extra_data": {"payment_id": razorpay_payment_id}})
                raise PaymentException(message="Invalid payment signature", code="PAYMENT_FAILED")
        else:
            logger.info("Mock payment verification signature check bypassed.")

        order = self.order_repo.get_by_uuid(user_id, order_uuid)
        if not order or order.razorpay_order_id != razorpay_order_id:
            raise PaymentException(message="Order mismatch", code="PAYMENT_FAILED")

        payment = self.payment_repo.get_by_idempotency(f"pay_init:{order.id}:{razorpay_order_id}")
        if not payment:
            raise PaymentException(message="Payment record not found", code="PAYMENT_FAILED")

        if payment.payment_status == PaymentStatus.SUCCESS:
            return OrderService(self._db)._serialize_order(order, include_timeline=True)

        if not self.mock_mode:
            rp_payment = self.client.payment.fetch(razorpay_payment_id)
            if rp_payment.get("status") != "captured":
                payment.failure_reason = f"Status: {rp_payment.get('status')}"
                payment.payment_status = PaymentStatus.FAILED
                payment.gateway_response = rp_payment
                payment.save()
                self.order_repo.add_timeline(order.id, OrderStatus.FAILED, "Payment not captured")
                raise PaymentException(message="Payment not captured", code="PAYMENT_FAILED")
        else:
            rp_payment = {
                "id": razorpay_payment_id,
                "status": "captured",
                "amount": rupees_to_paise(float(order.total_amount)),
                "currency": settings.CURRENCY,
                "method": "mock",
            }

        def _confirm_payment():
            self.payment_repo.mark_success(payment, razorpay_payment_id, razorpay_signature, rp_payment)
            self.order_repo.mark_payment_success(order, razorpay_payment_id)
            self.order_repo.add_timeline(
                order.id,
                OrderStatus.PAYMENT_SUCCESS,
                "Payment successful (Mock)" if self.mock_mode else "Payment successful"
            )
            next_status = (
                OrderStatus.COURT_PROCESSING
                if order.order_type == OrderType.COURT_SETTLEMENT
                else OrderStatus.UNDER_REVIEW
            )
            self.order_repo.update_status(order, next_status)
            self.order_repo.add_timeline(order.id, next_status, "Order moved to processing")

        self._db.run_in_transaction(_confirm_payment)

        # Post-payment workflow runs after commit (still synchronous, no Celery)
        self._db.on_commit(lambda: self.workflow.process_after_successful_payment(order.id))

        order.refresh_from_db()
        return OrderService(self._db)._serialize_order(order, include_timeline=True)

    def handle_webhook(self, payload: dict, signature: str) -> None:
        log = self.payment_repo.log_webhook(payload.get("event", "unknown"), payload, signature)
        try:
            body = payload if isinstance(payload, str) else json.dumps(payload)
            self.client.utility.verify_webhook_signature(body, signature, settings.RAZORPAY_WEBHOOK_SECRET)
        except Exception as exc:
            log.error_message = str(exc)
            log.save()
            raise PaymentException(message="Invalid webhook signature") from exc

        event = payload.get("event", "")
        if event == "payment.captured":
            entity = payload["payload"]["payment"]["entity"]
            order = self.order_repo.get_by_razorpay_order_id(entity.get("order_id", ""))
            if order and order.payment_status != PaymentStatus.SUCCESS:
                logger.info("Webhook payment.captured — reconcile", extra={"extra_data": {"order_id": order.id}})
        log.processed = True
        log.save()

    def _verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        body = f"{order_id}|{payment_id}"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _checkout_payload(self, order) -> dict:
        return {
            "order_uuid": str(order.uuid),
            "razorpay_order_id": order.razorpay_order_id,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount_paise": rupees_to_paise(float(order.total_amount)),
            "currency": settings.CURRENCY,
            "description": f"DriveClear — {order.order_type}",
        }
