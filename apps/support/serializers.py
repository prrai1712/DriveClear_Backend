from rest_framework import serializers

from apps.support.models import SupportTicket


class CreateTicketSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=200)
    description = serializers.CharField()
    order_id = serializers.IntegerField(required=False, allow_null=True)


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ("id", "order_id", "ticket_status", "subject", "description", "created_at", "updated_at")
