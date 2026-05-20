import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("driveclear")

RATE_LIMIT_RULES = {
    "/api/v1/auth/otp/send/": {"limit": 5, "window": 3600, "key": "otp_send"},
    "/api/v1/challans/fetch/": {"limit": 20, "window": 3600, "key": "challan_fetch"},
}


class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if settings.DEBUG:
            return None

        path = request.path
        rule = None
        for pattern, r in RATE_LIMIT_RULES.items():
            if path.startswith(pattern.rstrip("/")) or path == pattern:
                rule = r
                break
        if not rule:
            return None

        identifier = self._identifier(request, rule["key"])
        cache_key = f"rl:{rule['key']}:{identifier}"
        count = cache.get(cache_key, 0)
        if count >= rule["limit"]:
            logger.warning(
                "Rate limit exceeded",
                extra={"extra_data": {"path": path, "identifier": identifier}},
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "Too many requests. Please try again later.",
                    "data": None,
                    "meta": {"retry_after_seconds": rule["window"]},
                    "error": {"code": "RATE_LIMITED", "details": ""},
                },
                status=429,
            )
        cache.set(cache_key, count + 1, timeout=rule["window"])
        return None

    def _identifier(self, request, key: str) -> str:
        if key == "otp_send":
            body = {}
            if request.content_type == "application/json" and request.body:
                import json

                try:
                    body = json.loads(request.body)
                except json.JSONDecodeError:
                    pass
            phone = body.get("phone_number", "")
            return hashlib.sha256(phone.encode()).hexdigest()[:16]
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        return self._client_ip(request)

    @staticmethod
    def _client_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
