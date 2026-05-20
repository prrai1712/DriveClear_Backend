from rest_framework.views import APIView

from apps.orders.serializers import CreateOrderSerializer, PreviewCheckoutSerializer
from apps.orders.services.order_service import OrderService
from common.responses.api_response import success_response


class PreviewCheckoutView(APIView):
    def post(self, request):
        serializer = PreviewCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = OrderService().preview_checkout(
            request.user,
            [str(u) for u in serializer.validated_data["challan_uuids"]],
        )
        return success_response(message="Checkout preview", data=data)


class CreateOrderView(APIView):
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = OrderService().create_order(
            user=request.user,
            challan_uuid=str(serializer.validated_data["challan_uuid"]),
            order_type=serializer.validated_data["order_type"],
            idempotency_key=serializer.validated_data.get("idempotency_key"),
        )
        return success_response(message="Order created", data=data, status_code=201)


class MyOrdersView(APIView):
    def get(self, request):
        orders = OrderService().list_orders(request.user.id)
        return success_response(message="Orders fetched", data=orders, meta={"count": len(orders)})


class OrderDetailView(APIView):
    def get(self, request, order_uuid):
        data = OrderService().get_order_detail(request.user.id, order_uuid)
        return success_response(message="Order details", data=data)
