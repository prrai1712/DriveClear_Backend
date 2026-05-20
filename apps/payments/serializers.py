from rest_framework import serializers


class CreateRazorpayOrderSerializer(serializers.Serializer):
    order_uuid = serializers.UUIDField()


class VerifyPaymentSerializer(serializers.Serializer):
    order_uuid = serializers.UUIDField()
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class CheckoutInitiateSerializer(serializers.Serializer):
    challan_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
    )
    checkout_idempotency_key = serializers.CharField(max_length=64)


class CheckoutVerifySerializer(serializers.Serializer):
    checkout_batch_id = serializers.UUIDField()
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
