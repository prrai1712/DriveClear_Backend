import logging
import random
import string

from django.conf import settings
from django.core.cache import cache

from apps.auth.models import OTPAuditLog
from common.exceptions.base import RateLimitException, ValidationException
from common.validators.phone import normalize_phone

logger = logging.getLogger("driveclear")

OTP_CACHE_PREFIX = "otp:"
OTP_ATTEMPT_PREFIX = "otp_attempts:"
OTP_DAILY_PREFIX = "otp_daily:"


class OTPService:
    def send_otp(self, phone_number: str, ip_address: str | None = None) -> dict:
        phone = normalize_phone(phone_number)

        daily_key = f"{OTP_DAILY_PREFIX}{phone}"
        daily_count = cache.get(daily_key, 0)
        if daily_count >= settings.OTP_DAILY_LIMIT_PER_PHONE:
            self._audit(phone, "rate_limited", ip_address)
            raise RateLimitException(
                message="Daily OTP limit reached",
                code="OTP_RATE_LIMIT",
            )

        cooldown_key = f"otp_cooldown:{phone}"
        if cache.get(cooldown_key):
            raise RateLimitException(
                message="Please wait before requesting another OTP",
                code="OTP_RATE_LIMIT",
            )

        otp = self._generate_otp()
        cache.set(f"{OTP_CACHE_PREFIX}{phone}", otp, timeout=settings.OTP_TTL_SECONDS)
        cache.set(cooldown_key, "1", timeout=settings.OTP_RESEND_COOLDOWN_SECONDS)
        cache.set(daily_key, daily_count + 1, timeout=86400)
        cache.set(f"{OTP_ATTEMPT_PREFIX}{phone}", 0, timeout=settings.OTP_TTL_SECONDS)

        self._dispatch_sms(phone, otp)
        self._audit(phone, "sent", ip_address)

        logger.info("OTP sent", extra={"extra_data": {"phone_suffix": phone[-4:]}})
        payload: dict = {"expires_in_seconds": settings.OTP_TTL_SECONDS}
        # Local dev only — never enable in production
        if settings.DEBUG and settings.SMS_PROVIDER == "mock":
            payload["dev_otp"] = otp
            payload["dev_note"] = "SMS_PROVIDER=mock — no SMS sent. Use dev_otp to verify."
        return payload

    def verify_otp(self, phone_number: str, otp: str, ip_address: str | None = None) -> bool:
        phone = normalize_phone(phone_number)
        cache_key = f"{OTP_CACHE_PREFIX}{phone}"
        stored = cache.get(cache_key)

        if not stored:
            self._audit(phone, "failed", ip_address, {"reason": "expired"})
            raise ValidationException(message="OTP expired", code="OTP_EXPIRED")

        attempt_key = f"{OTP_ATTEMPT_PREFIX}{phone}"
        attempts = cache.get(attempt_key, 0)
        if attempts >= settings.OTP_MAX_ATTEMPTS:
            cache.delete(cache_key)
            self._audit(phone, "failed", ip_address, {"reason": "max_attempts"})
            raise ValidationException(message="Too many invalid attempts", code="OTP_INVALID")

        if stored != otp.strip():
            cache.set(attempt_key, attempts + 1, timeout=settings.OTP_TTL_SECONDS)
            self._audit(phone, "failed", ip_address, {"reason": "mismatch"})
            raise ValidationException(message="Invalid OTP", code="OTP_INVALID")

        cache.delete(cache_key)
        cache.delete(attempt_key)
        self._audit(phone, "verified", ip_address)
        return True

    def _generate_otp(self) -> str:
        if settings.SMS_PROVIDER == "mock":
            return "123456"
        return "".join(random.choices(string.digits, k=settings.OTP_LENGTH))

    def _dispatch_sms(self, phone: str, otp: str) -> None:
        provider = settings.SMS_PROVIDER

        if provider == "mock":
            logger.info(
                "Mock SMS OTP",
                extra={"extra_data": {"phone_suffix": phone[-4:], "otp": otp if settings.DEBUG else "****"}},
            )
            return

        if provider == "msg91":
            from apps.auth.services.sms.msg91_provider import MSG91Provider

            MSG91Provider().send_otp(phone, otp)
            return

        raise NotImplementedError(f"Unknown SMS_PROVIDER: {provider}. Use mock or msg91.")

    def _audit(self, phone: str, event: str, ip: str | None, metadata: dict | None = None) -> None:
        OTPAuditLog.objects.create(
            phone_number=phone,
            event=event,
            ip_address=ip,
            metadata=metadata or {},
        )
