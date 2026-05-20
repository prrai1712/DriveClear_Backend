from rest_framework import serializers

from common.constants.enums import VehicleType
from common.validators.vehicle import validate_vehicle_number


class FetchChallanSerializer(serializers.Serializer):
    vehicle_number = serializers.CharField(max_length=12)
    vehicle_type = serializers.ChoiceField(choices=VehicleType.choices, default=VehicleType.PRIVATE)

    def validate_vehicle_number(self, value):
        return validate_vehicle_number(value)
