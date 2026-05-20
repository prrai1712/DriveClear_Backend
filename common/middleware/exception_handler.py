import json
import logging

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from common.exceptions.base import DriveClearException
from common.responses.api_response import error_response

logger = logging.getLogger("driveclear")


class ExceptionMiddleware(MiddlewareMixin):
    """Catch non-DRF exceptions and return standardized JSON."""

    def process_exception(self, request, exception):
        if isinstance(exception, DriveClearException):
            response = error_response(
                message=exception.message,
                code=exception.code,
                details=exception.details,
                status_code=exception.status_code,
            )
            return JsonResponse(response.data, status=response.status_code)

        logger.exception("Unhandled middleware exception", extra={"path": request.path})
        response = error_response(
            message="Internal server error",
            code="INTERNAL_ERROR",
            status_code=500,
        )
        return JsonResponse(json.loads(response.rendered_content), status=500)
