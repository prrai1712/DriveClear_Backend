"""Run via cron on Render: python manage.py cleanup_stale_orders"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from common.constants.enums import OrderStatus, PaymentStatus
from common.database.db_manager import get_db_manager


class Command(BaseCommand):
    help = "Mark payment-pending orders older than 24h as FAILED"

    def handle(self, *args, **options):
        db = get_db_manager()
        cutoff = timezone.now() - timedelta(hours=24)

        def _cleanup():
            return Order.objects.filter(
                order_status=OrderStatus.PAYMENT_PENDING,
                payment_status=PaymentStatus.INITIATED,
                created_at__lt=cutoff,
            ).update(order_status=OrderStatus.FAILED)

        count = db.run_in_transaction(_cleanup)
        self.stdout.write(self.style.SUCCESS(f"Marked {count} orders as FAILED"))
