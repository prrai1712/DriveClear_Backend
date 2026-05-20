from django.contrib import admin

from apps.orders.models import Order, OrderTimeline


class OrderTimelineInline(admin.TabularInline):
    model = OrderTimeline
    extra = 0
    readonly_fields = ("status", "message", "metadata", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("uuid", "order_type", "order_status", "payment_status", "total_amount", "user", "created_at")
    list_filter = ("order_status", "payment_status", "order_type")
    search_fields = ("uuid", "razorpay_order_id", "razorpay_payment_id", "user__phone_number")
    inlines = [OrderTimelineInline]
