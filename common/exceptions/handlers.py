import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler as drf_default_handler

from common.exceptions.base import DriveClearException
from common.responses.api_response import error_response

logger = logging.getLogger("driveclear")


def drf_exception_handler(exc, context):
    """Centralized DRF exception → standardized envelope."""
    if isinstance(exc, DriveClearException):
        return error_response(
            message=exc.message,
            code=exc.code,
            details=exc.details,
            status_code=exc.status_code,
        )

    if isinstance(exc, ValidationError):
        return error_response(
            message="Validation failed",
            code="VALIDATION_ERROR",
            details=exc.detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, (Http404,)):
        return error_response(
            message="Resource not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        return error_response(
            message="Permission denied",
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    response = drf_default_handler(exc, context)

    if response is not None:
        if isinstance(exc, APIException):
            return error_response(
                message=str(exc.detail) if not isinstance(exc.detail, dict) else "Request failed",
                code=getattr(exc, "default_code", "API_ERROR").upper(),
                details=exc.detail if isinstance(exc.detail, dict) else str(exc.detail),
                status_code=response.status_code,
            )
        return response

    # Unhandled — mask internals
    request = context.get("request")
    logger.exception(
        "Unhandled exception",
        extra={
            "path": getattr(request, "path", None),
            "method": getattr(request, "method", None),
        },
    )
    return error_response(
        message="Internal server error",
        code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
