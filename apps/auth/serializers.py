from rest_framework import serializers

from common.validators.phone import validate_indian_phone


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)

    def validate_phone_number(self, value):
        return validate_indian_phone(value)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(min_length=4, max_length=8)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    device_id = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    device_platform = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")

    def validate_phone_number(self, value):
        return validate_indian_phone(value)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class FirebaseVerifySerializer(serializers.Serializer):
    id_token = serializers.CharField()
    name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    device_id = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    device_platform = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
