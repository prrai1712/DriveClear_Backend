import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("driveclear")


class DeviceTrackingMiddleware(MiddlewareMixin):
    """Attach device metadata for fraud detection and session tracking."""

    def process_request(self, request):
        request.device_id = request.headers.get("X-Device-ID", "")
        request.device_platform = request.headers.get("X-Device-Platform", "")  # ios | android | web
        request.app_version = request.headers.get("X-App-Version", "")

        if request.user.is_authenticated and request.device_id:
            from apps.auth.repositories.device_session_repository import DeviceSessionRepository

            DeviceSessionRepository().touch(
                user_id=request.user.id,
                device_id=request.device_id,
                platform=request.device_platform,
                ip=self._client_ip(request),
            )

    @staticmethod
    def _client_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
