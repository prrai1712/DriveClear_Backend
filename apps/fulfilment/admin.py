from django.contrib import admin

from apps.fulfilment.models import ChallanFulfilment


@admin.register(ChallanFulfilment)
class ChallanFulfilmentAdmin(admin.ModelAdmin):
    list_display = (
        "challan_number",
        "vehicle_number",
        "fulfilment_status",
        "refund_status",
        "total_paid",
        "paid_at",
        "created_at",
    )
    list_filter = ("fulfilment_status", "refund_status", "order_type")
    search_fields = ("challan_number", "vehicle_number", "razorpay_payment_id", "order__uuid")
    readonly_fields = ("uuid", "idempotency_key", "created_at", "updated_at")
    raw_id_fields = ("user", "order", "challan", "vehicle")
