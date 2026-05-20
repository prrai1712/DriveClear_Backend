"""Helpers for pending vs paid challan counts from normalized API rows."""

PENDING_STATUSES = frozenset({"PENDING", "UNPAID", "OPEN"})


def is_pending_normalized(item: dict) -> bool:
    status = str(item.get("status") or "PENDING").upper()
    return status in PENDING_STATUSES


def count_pending_normalized(items: list[dict]) -> int:
    return sum(1 for item in items if is_pending_normalized(item))


def count_pending_serialized(items: list[dict]) -> int:
    return sum(
        1
        for item in items
        if str(item.get("challan_status") or item.get("status") or "").upper() in PENDING_STATUSES
    )
