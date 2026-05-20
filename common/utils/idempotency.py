from django.core.cache import cache


def acquire_idempotency_lock(key: str, ttl: int = 300) -> bool:
    """Returns True if lock acquired (first request), False if duplicate."""
    cache_key = f"idempotency:{key}"
    return cache.add(cache_key, "1", timeout=ttl)


def release_idempotency_lock(key: str) -> None:
    cache.delete(f"idempotency:{key}")
