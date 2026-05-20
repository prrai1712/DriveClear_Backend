from django.contrib import admin

from apps.payments.models import Payment, PaymentWebhookLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "payment_status", "amount", "gateway_payment_id", "created_at")
    list_filter = ("payment_status",)
    search_fields = ("gateway_order_id", "gateway_payment_id")


@admin.register(PaymentWebhookLog)
class PaymentWebhookLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "processed", "created_at")
    list_filter = ("processed", "event_type")
