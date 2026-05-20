import re

from django.core.exceptions import ValidationError

INDIAN_MOBILE_REGEX = re.compile(r"^[6-9]\d{9}$")


def validate_indian_phone(value: str) -> str:
    cleaned = re.sub(r"\D", "", value or "")
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    if not INDIAN_MOBILE_REGEX.match(cleaned):
        raise ValidationError("Invalid Indian mobile number")
    return cleaned


def normalize_phone(value: str) -> str:
    return validate_indian_phone(value)
