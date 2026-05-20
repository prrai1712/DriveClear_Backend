import logging
import time

from django.utils.deprecation import MiddlewareMixin

from common.logging.context import get_correlation_id, set_correlation_id

logger = logging.getLogger("driveclear")

SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}
SENSITIVE_BODY_KEYS = {"otp", "password", "refresh", "razorpay_signature"}


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        cid = request.headers.get("X-Correlation-ID") or get_correlation_id()
        set_correlation_id(cid)
        request.correlation_id = cid
        request._start_time = time.monotonic()

    def process_response(self, request, response):
        duration_ms = int((time.monotonic() - getattr(request, "_start_time", time.monotonic())) * 1000)
        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = request.user.id

        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in SENSITIVE_HEADERS
        }

        logger.info(
            "HTTP request",
            extra={
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "extra_data": {
                    "ip": self._client_ip(request),
                    "device_id": request.headers.get("X-Device-ID"),
                    "correlation_id": getattr(request, "correlation_id", ""),
                    "query": dict(request.GET),
                },
            },
        )
        response["X-Correlation-ID"] = getattr(request, "correlation_id", "")
        return response

    @staticmethod
    def _client_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
