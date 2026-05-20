from django.contrib import admin

from apps.challans.models import ChallanDetail, ChallanFetchRequest


@admin.register(ChallanDetail)
class ChallanDetailAdmin(admin.ModelAdmin):
    list_display = ("challan_number", "vehicle_number", "total_amount", "challan_status", "user", "fetched_at")
    search_fields = ("challan_number", "vehicle_number", "uuid")
    list_filter = ("challan_status", "payment_status", "is_court_challan")


@admin.register(ChallanFetchRequest)
class ChallanFetchRequestAdmin(admin.ModelAdmin):
    list_display = ("vehicle_number", "status", "retry_count", "user", "created_at")
    list_filter = ("status",)
