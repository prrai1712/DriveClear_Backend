from django.conf import settings
from django.db import models

from apps.core.models.base import TimeStampedModel
from common.constants.enums import TicketStatus


class SupportTicket(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True)
    ticket_status = models.CharField(max_length=32, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    admin_notes = models.TextField(blank=True)

    class Meta:
        db_table = "support_tickets"
        indexes = [
            models.Index(fields=["user", "ticket_status"]),
            models.Index(fields=["created_at"]),
        ]
