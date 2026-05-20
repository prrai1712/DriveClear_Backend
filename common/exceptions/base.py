from rest_framework import status


class DriveClearException(Exception):
    """Base application exception."""

    default_message = "Something went wrong"
    default_code = "INTERNAL_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message=None, code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details
        super().__init__(self.message)


class ValidationException(DriveClearException):
    default_message = "Validation failed"
    default_code = "VALIDATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundException(DriveClearException):
    default_message = "Resource not found"
    default_code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class UnauthorizedException(DriveClearException):
    default_message = "Unauthorized"
    default_code = "UNAUTHORIZED"
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenException(DriveClearException):
    default_message = "Forbidden"
    default_code = "FORBIDDEN"
    status_code = status.HTTP_403_FORBIDDEN


class RateLimitException(DriveClearException):
    default_message = "Too many requests"
    default_code = "RATE_LIMITED"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class ExternalAPIException(DriveClearException):
    default_message = "External service unavailable"
    default_code = "EXTERNAL_API_ERROR"
    status_code = status.HTTP_502_BAD_GATEWAY


class PaymentException(DriveClearException):
    default_message = "Payment processing failed"
    default_code = "PAYMENT_FAILED"
    status_code = status.HTTP_402_PAYMENT_REQUIRED
