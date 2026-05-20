from rest_framework.views import APIView

from apps.support.models import SupportTicket
from apps.support.serializers import CreateTicketSerializer, TicketSerializer
from common.responses.api_response import success_response


class CreateTicketView(APIView):
    def post(self, request):
        serializer = CreateTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = SupportTicket.objects.create(
            user=request.user,
            order_id=serializer.validated_data.get("order_id"),
            subject=serializer.validated_data["subject"],
            description=serializer.validated_data["description"],
        )
        return success_response(
            message="Support ticket created",
            data=TicketSerializer(ticket).data,
            status_code=201,
        )


class ListTicketsView(APIView):
    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user).order_by("-created_at")
        return success_response(
            message="Tickets fetched",
            data=TicketSerializer(tickets, many=True).data,
        )
