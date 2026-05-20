import json

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.payments.serializers import (
    CheckoutInitiateSerializer,
    CheckoutVerifySerializer,
    CreateRazorpayOrderSerializer,
    VerifyPaymentSerializer,
)
from apps.payments.services.checkout_payment_service import CheckoutPaymentService
from apps.payments.services.razorpay_service import RazorpayService
from common.responses.api_response import success_response


class CheckoutInitiateView(APIView):
    """Create orders + single Razorpay order for selected challans."""

    def post(self, request):
        serializer = CheckoutInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = CheckoutPaymentService().initiate_checkout(
            request.user,
            [str(u) for u in serializer.validated_data["challan_uuids"]],
            serializer.validated_data["checkout_idempotency_key"],
        )
        return success_response(message="Checkout ready", data=data)


class CheckoutVerifyView(APIView):
    """Verify Razorpay payment and confirm all orders in the batch."""

    def post(self, request):
        serializer = CheckoutVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = CheckoutPaymentService().verify_checkout(
            user_id=request.user.id,
            checkout_batch_id=str(serializer.validated_data["checkout_batch_id"]),
            razorpay_order_id=serializer.validated_data["razorpay_order_id"],
            razorpay_payment_id=serializer.validated_data["razorpay_payment_id"],
            razorpay_signature=serializer.validated_data["razorpay_signature"],
        )
        return success_response(message="Payment successful", data=data)


class CreateRazorpayOrderView(APIView):
    def post(self, request):
        serializer = CreateRazorpayOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = RazorpayService().create_razorpay_order(
            request.user,
            str(serializer.validated_data["order_uuid"]),
        )
        return success_response(message="Razorpay order created", data=data)


class VerifyPaymentView(APIView):
    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = RazorpayService().verify_payment(
            order_uuid=str(serializer.validated_data["order_uuid"]),
            user_id=request.user.id,
            razorpay_order_id=serializer.validated_data["razorpay_order_id"],
            razorpay_payment_id=serializer.validated_data["razorpay_payment_id"],
            razorpay_signature=serializer.validated_data["razorpay_signature"],
        )
        return success_response(message="Payment verified", data=data)


class RazorpayWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.headers.get("X-Razorpay-Signature", "")
        payload = request.data if isinstance(request.data, dict) else json.loads(request.body)
        RazorpayService().handle_webhook(payload, signature)
        return success_response(message="Webhook processed")
