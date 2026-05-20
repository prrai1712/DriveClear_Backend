import uuid

from django.utils import timezone

from apps.orders.models import Order, OrderTimeline
from common.constants.enums import OrderStatus, PaymentStatus
from common.database.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    def create_order(self, **kwargs) -> Order:
        if "idempotency_key" not in kwargs:
            kwargs["idempotency_key"] = str(uuid.uuid4())
        return Order.objects.create(**kwargs)

    def get_by_uuid(self, user_id: int, order_uuid: str) -> Order | None:
        return Order.objects.filter(user_id=user_id, uuid=order_uuid).select_related("challan").first()

    def get_by_idempotency(self, key: str) -> Order | None:
        return Order.objects.filter(idempotency_key=key).first()

    def get_by_razorpay_order_id(self, razorpay_order_id: str) -> Order | None:
        return Order.objects.filter(razorpay_order_id=razorpay_order_id).first()

    def list_by_razorpay_order_id(self, razorpay_order_id: str):
        return Order.objects.filter(razorpay_order_id=razorpay_order_id).select_related("challan")

    def list_by_checkout_batch(self, user_id: int, checkout_batch_id):
        return (
            Order.objects.filter(user_id=user_id, checkout_batch_id=checkout_batch_id)
            .select_related("challan")
            .order_by("id")
        )

    def list_for_user(self, user_id: int):
        return (
            Order.objects.filter(user_id=user_id)
            .select_related("challan")
            .prefetch_related("timeline", "payments")
            .order_by("-created_at")
        )

    def update_status(self, order: Order, order_status: str, payment_status: str | None = None) -> Order:
        order.order_status = order_status
        update_fields = ["order_status", "updated_at"]
        if payment_status:
            order.payment_status = payment_status
            update_fields.append("payment_status")
        order.save(update_fields=update_fields)
        return order

    def add_timeline(self, order_id: int, status: str, message: str, metadata: dict | None = None) -> OrderTimeline:
        return OrderTimeline.objects.create(
            order_id=order_id,
            status=status,
            message=message,
            metadata=metadata or {},
        )

    def mark_payment_success(self, order: Order, razorpay_payment_id: str) -> Order:
        order.order_status = OrderStatus.PAYMENT_SUCCESS
        order.payment_status = PaymentStatus.SUCCESS
        order.razorpay_payment_id = razorpay_payment_id
        order.payment_completed_at = timezone.now()
        order.save(
            update_fields=[
                "order_status",
                "payment_status",
                "razorpay_payment_id",
                "payment_completed_at",
                "updated_at",
            ]
        )
        return order
