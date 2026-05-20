from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from common.database.db_manager import get_db_manager
from common.responses.api_response import error_response, success_response


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        db_status = get_db_manager().health_check()
        redis_ok = True
        try:
            cache.set("health_ping", "1", 5)
            redis_ok = cache.get("health_ping") == "1"
        except Exception:
            redis_ok = False

        healthy = db_status.get("connected") and redis_ok
        payload = {
            "database": db_status.get("connected", False),
            "redis": redis_ok,
            "status": "healthy" if healthy else "degraded",
        }
        if healthy:
            return success_response(message="OK", data=payload)
        return error_response(message="Degraded", code="HEALTH_DEGRADED", status_code=503)
