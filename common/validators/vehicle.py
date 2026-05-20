import re

from django.core.exceptions import ValidationError

# Indian vehicle: DL01AB1234, MH12DE1433, etc.
VEHICLE_REGEX = re.compile(
    r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$|"
    r"^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$",
    re.IGNORECASE,
)


def validate_vehicle_number(value: str) -> str:
    cleaned = (value or "").strip().upper().replace(" ", "").replace("-", "")
    if not cleaned or len(cleaned) < 6 or len(cleaned) > 12:
        raise ValidationError("Invalid vehicle number format")
    if not VEHICLE_REGEX.match(cleaned):
        raise ValidationError("Invalid vehicle number format")
    return cleaned
