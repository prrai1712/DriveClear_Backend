from rest_framework import serializers

from apps.users.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("uuid", "name", "phone_number", "is_phone_verified", "last_login", "created_at")
