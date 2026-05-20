from rest_framework import serializers

from common.constants.enums import OrderType


class CreateOrderSerializer(serializers.Serializer):
    challan_uuid = serializers.UUIDField()
    order_type = serializers.ChoiceField(choices=OrderType.choices)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)


class PreviewCheckoutSerializer(serializers.Serializer):
    challan_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
    )
