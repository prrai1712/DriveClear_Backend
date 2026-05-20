import uuid
from decimal import Decimal

from apps.challans.repositories.challan_repository import ChallanRepository
from apps.orders.repositories.order_repository import OrderRepository
from common.constants.enums import OrderStatus, OrderType, PaymentStatus, SettlementStatus
from common.database.db_manager import get_db_manager
from common.database.interfaces import IDatabaseManager
from common.exceptions.base import NotFoundException, PaymentException, ValidationException
from common.utils.idempotency import acquire_idempotency_lock


class OrderService:
    FEE_MAP = {
        OrderType.ONLINE_PAYMENT: Decimal("99.00"),
        OrderType.COURT_SETTLEMENT: Decimal("999.00"),
    }

    def __init__(self, db: IDatabaseManager | None = None):
        self._db = db or get_db_manager()
        self.order_repo = OrderRepository(self._db)
        self.challan_repo = ChallanRepository(self._db)

    def preview_checkout(self, user, challan_uuids: list) -> dict:
        """Quote line items + fees without creating orders."""
        line_items = []
        subtotal_challans = Decimal("0")
        subtotal_fees = Decimal("0")

        for challan_uuid in challan_uuids:
            challan = self.challan_repo.get_by_uuid(str(challan_uuid))
            if not challan:
                raise NotFoundException(message=f"Challan not found: {challan_uuid}")

            status = (challan.challan_status or "").upper()
            if status not in ("PENDING",):
                if status == "OPS_PENDING":
                    raise ValidationException(
                        message=f"Challan {challan.challan_number} is already paid and awaiting settlement",
                        code="CHALLAN_ALREADY_PAID",
                    )
                raise ValidationException(
                    message=f"Challan {challan.challan_number} is not payable (status: {challan.challan_status})",
                    code="CHALLAN_NOT_PAYABLE",
                )

            if challan.total_amount <= 0:
                raise ValidationException(
                    message=f"We do not accept payment for challan {challan.challan_number} (zero amount)",
                    code="CHALLAN_ZERO_AMOUNT",
                )

            order_type = (
                OrderType.COURT_SETTLEMENT if challan.is_court_challan else OrderType.ONLINE_PAYMENT
            )
            medium = "court_challan" if challan.is_court_challan else "online_challan"
            fee = self.FEE_MAP[order_type]
            payable = challan.total_amount
            line_total = payable + fee

            subtotal_challans += payable
            subtotal_fees += fee

            offences = challan.offence_details or []
            offense_name = offences[0].get("name") if offences else ""

            line_items.append(
                {
                    "challan_uuid": str(challan.uuid),
                    "challan_number": challan.challan_number,
                    "vehicle_number": challan.vehicle_number,
                    "offense_name": offense_name,
                    "place": challan.city_name,
                    "issue_date": str(challan.issue_date) if challan.issue_date else "",
                    "is_court_challan": challan.is_court_challan,
                    "medium": medium,
                    "order_type": order_type,
                    "challan_amount": str(payable),
                    "service_fee": str(fee),
                    "line_total": str(line_total),
                }
            )

        grand_total = subtotal_challans + subtotal_fees
        return {
            "line_items": line_items,
            "challan_count": len(line_items),
            "subtotal_challans": str(subtotal_challans),
            "subtotal_service_fees": str(subtotal_fees),
            "grand_total": str(grand_total),
            "fee_note": "₹99 per online challan · ₹999 per court challan",
        }

    def create_orders_for_checkout(
        self,
        user,
        challan_uuids: list[str],
        checkout_batch_id,
        checkout_idempotency_key: str,
    ) -> list:
        """Create one DriveClear order per challan (idempotent per challan in batch)."""
        batch_uuid = (
            checkout_batch_id
            if isinstance(checkout_batch_id, uuid.UUID)
            else uuid.UUID(str(checkout_batch_id))
        )
        orders = []
        preview = self.preview_checkout(user, challan_uuids)

        for item in preview["line_items"]:
            challan_uuid = item["challan_uuid"]
            order_type = item["order_type"]
            idem = f"checkout:{checkout_idempotency_key}:{challan_uuid}"

            existing = self.order_repo.get_by_idempotency(idem)
            if existing:
                if existing.payment_status == PaymentStatus.SUCCESS:
                    raise ValidationException(
                        message=f"Challan {item['challan_number']} is already paid",
                        code="CHALLAN_ALREADY_PAID",
                    )
                if existing.checkout_batch_id != batch_uuid:
                    existing.checkout_batch_id = batch_uuid
                    existing.save(update_fields=["checkout_batch_id", "updated_at"])
                orders.append(existing)
                continue

            challan = self.challan_repo.get_by_uuid(challan_uuid)
            fee = self.FEE_MAP[order_type]
            payable = challan.total_amount
            total = payable + fee
            settlement = (
                SettlementStatus.PENDING
                if order_type == OrderType.COURT_SETTLEMENT
                else SettlementStatus.NOT_APPLICABLE
            )

            def _create(
                ch_id=challan.id,
                otype=order_type,
                pay=payable,
                f=fee,
                tot=total,
                sett=settlement,
                key=idem,
                batch=batch_uuid,
            ):
                order = self.order_repo.create_order(
                    user_id=user.id,
                    challan_id=ch_id,
                    order_type=otype,
                    order_status=OrderStatus.CREATED,
                    payable_amount=pay,
                    convenience_fee=f,
                    total_amount=tot,
                    settlement_status=sett,
                    idempotency_key=key,
                    checkout_batch_id=batch,
                )
                self.order_repo.add_timeline(order.id, OrderStatus.CREATED, "Order created for checkout")
                self.order_repo.update_status(order, OrderStatus.PAYMENT_PENDING)
                return order

            order = self._db.run_in_transaction(_create)
            orders.append(order)

        return orders

    def create_order(
        self,
        user,
        challan_uuid: str,
        order_type: str,
        idempotency_key: str | None = None,
    ) -> dict:
        key = idempotency_key or str(uuid.uuid4())
        if not acquire_idempotency_lock(f"order_create:{key}", ttl=300):
            existing = self.order_repo.get_by_idempotency(key)
            if existing:
                return self._serialize_order(existing)
            raise PaymentException(message="Duplicate request in progress", code="PAYMENT_DUPLICATE")

        existing = self.order_repo.get_by_idempotency(key)
        if existing:
            return self._serialize_order(existing)

        challan = self.challan_repo.get_by_uuid(challan_uuid)
        if not challan:
            raise NotFoundException(message="Challan not found")

        if challan.total_amount <= 0:
            raise ValidationException(
                message=f"We do not accept payment for challan {challan.challan_number} (zero amount)",
                code="CHALLAN_ZERO_AMOUNT",
            )

        if order_type not in self.FEE_MAP:
            raise ValidationException(message="Invalid order type")

        fee = self.FEE_MAP[order_type]
        payable = challan.total_amount
        total = payable + fee

        settlement = (
            SettlementStatus.PENDING
            if order_type == OrderType.COURT_SETTLEMENT
            else SettlementStatus.NOT_APPLICABLE
        )

        def _create():
            order = self.order_repo.create_order(
                user_id=user.id,
                challan_id=challan.id,
                order_type=order_type,
                order_status=OrderStatus.CREATED,
                payable_amount=payable,
                convenience_fee=fee,
                total_amount=total,
                settlement_status=settlement,
                idempotency_key=key,
            )
            self.order_repo.add_timeline(order.id, OrderStatus.CREATED, "Order created")
            self.order_repo.update_status(order, OrderStatus.PAYMENT_PENDING)
            return order

        order = self._db.run_in_transaction(_create)
        return self._serialize_order(order)

    def get_order_detail(self, user_id: int, order_uuid: str) -> dict:
        order = self.order_repo.get_by_uuid(user_id, order_uuid)
        if not order:
            raise NotFoundException(message="Order not found")
        return self._serialize_order(order, include_timeline=True)

    def list_orders(self, user_id: int) -> list[dict]:
        return [self._serialize_order(o, include_timeline=False) for o in self.order_repo.list_for_user(user_id)]

    def _serialize_order(self, order, include_timeline: bool = False) -> dict:
        data = {
            "uuid": str(order.uuid),
            "order_type": order.order_type,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "settlement_status": order.settlement_status,
            "payable_amount": str(order.payable_amount),
            "convenience_fee": str(order.convenience_fee),
            "total_amount": str(order.total_amount),
            "razorpay_order_id": order.razorpay_order_id,
            "payment_completed_at": order.payment_completed_at,
            "refund_status": order.refund_status,
            "created_at": order.created_at,
            "challan": {
                "uuid": str(order.challan.uuid),
                "challan_number": order.challan.challan_number,
                "vehicle_number": order.challan.vehicle_number,
            },
        }
        if include_timeline:
            data["timeline"] = [
                {
                    "status": t.status,
                    "message": t.message,
                    "metadata": t.metadata,
                    "created_at": t.created_at,
                }
                for t in order.timeline.all()
            ]
        return data
