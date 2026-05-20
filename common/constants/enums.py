from django.db import models


class UserRole(models.TextChoices):
    USER = "USER", "User"
    ADMIN = "ADMIN", "Admin"
    OPERATIONS = "OPERATIONS", "Operations"
    SUPPORT = "SUPPORT", "Support"


class OrderType(models.TextChoices):
    ONLINE_PAYMENT = "ONLINE_PAYMENT", "Online Challan Payment"
    COURT_SETTLEMENT = "COURT_SETTLEMENT", "Court Settlement Service"


class OrderStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Payment Pending"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS", "Payment Success"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    COURT_PROCESSING = "COURT_PROCESSING", "Court Processing"
    SETTLEMENT_IN_PROGRESS = "SETTLEMENT_IN_PROGRESS", "Settlement In Progress"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class PaymentStatus(models.TextChoices):
    INITIATED = "INITIATED", "Initiated"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class SettlementStatus(models.TextChoices):
    NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class RefundStatus(models.TextChoices):
    NONE = "NONE", "None"
    INITIATED = "INITIATED", "Initiated"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class ChallanStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    OPS_PENDING = "OPS_PENDING", "Operations Pending"
    PAID = "PAID", "Paid"
    DISPUTED = "DISPUTED", "Disputed"
    SETTLED = "SETTLED", "Settled"
    UNKNOWN = "UNKNOWN", "Unknown"


class FulfilmentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


class TicketStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    RESOLVED = "RESOLVED", "Resolved"
    CLOSED = "CLOSED", "Closed"


class VehicleType(models.TextChoices):
    PRIVATE = "private", "Private"
    COMMERCIAL = "commercial", "Commercial"


class FetchRequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    PARTIAL = "PARTIAL", "Partial"
    CACHED = "CACHED", "Cached"


class ChallanFetchSource(models.TextChoices):
    CHALLANPAY = "challanpay", "ChallanPay"


class ErrorCode:
    INVALID_PHONE = "INVALID_PHONE"
    INVALID_VEHICLE = "INVALID_VEHICLE"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_INVALID = "OTP_INVALID"
    OTP_RATE_LIMIT = "OTP_RATE_LIMIT"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_DUPLICATE = "PAYMENT_DUPLICATE"
    ORDER_INVALID_STATE = "ORDER_INVALID_STATE"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
