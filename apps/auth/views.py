from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.auth.serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    RefreshTokenSerializer,
    FirebaseVerifySerializer,
)
from apps.auth.services.auth_service import AuthService
from common.middleware.request_logging import RequestLoggingMiddleware
from common.responses.api_response import success_response, error_response


class SendOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # ignore stale Bearer on login

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = RequestLoggingMiddleware._client_ip(request)
        result = AuthService().send_otp(
            phone_number=serializer.validated_data["phone_number"],
            name=serializer.validated_data.get("name", ""),
            ip_address=ip,
        )
        return success_response(message="OTP sent successfully", data=result)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = RequestLoggingMiddleware._client_ip(request)
        data = AuthService().verify_otp_and_login(
            phone_number=serializer.validated_data["phone_number"],
            otp=serializer.validated_data["otp"],
            name=serializer.validated_data.get("name", ""),
            device_id=serializer.validated_data.get("device_id", ""),
            platform=serializer.validated_data.get("device_platform", ""),
            ip_address=ip,
        )
        return success_response(message="Login successful", data=data)


class FirebaseVerifyView(APIView):
    """Exchange Firebase phone-auth ID token for DriveClear JWT."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = FirebaseVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = RequestLoggingMiddleware._client_ip(request)
        data = AuthService().login_with_firebase(
            id_token=serializer.validated_data["id_token"],
            name=serializer.validated_data.get("name", ""),
            device_id=serializer.validated_data.get("device_id", ""),
            platform=serializer.validated_data.get("device_platform", ""),
            ip_address=ip,
        )
        return success_response(message="Login successful", data=data)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = AuthService().refresh_tokens(serializer.validated_data["refresh"])
        except TokenError:
            return error_response(message="Invalid refresh token", code="UNAUTHORIZED", status_code=401)
        return success_response(message="Token refreshed", data=tokens)


class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get("refresh")
        device_id = request.headers.get("X-Device-ID", "")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except TokenError:
                pass
        AuthService().logout(request.user.id, device_id)
        return success_response(message="Logged out successfully")
