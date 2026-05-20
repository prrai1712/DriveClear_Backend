from django.contrib import admin

from apps.support.models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "ticket_status", "user", "created_at")
    list_filter = ("ticket_status",)
    search_fields = ("subject", "user__phone_number")
