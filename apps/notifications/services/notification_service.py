import logging

from apps.notifications.models import NotificationLog

logger = logging.getLogger("driveclear")


class NotificationService:
    """Outbound notifications — integrate FCM / MSG91 here."""

    def notify_order_update(self, order) -> None:
        message = f"Order {order.order_status}: {order.challan.challan_number}"
        NotificationLog.objects.create(
            user_id=order.user_id,
            channel="push",
            event="order_status_update",
            payload={"order_uuid": str(order.uuid), "status": order.order_status},
            status="queued",
        )
        logger.info(
            "Notification queued",
            extra={"extra_data": {"user_id": order.user_id, "order_uuid": str(order.uuid)}},
        )
