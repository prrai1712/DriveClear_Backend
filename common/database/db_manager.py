"""
DatabaseManager — single responsibility: DB transactions and health.

Usage:
    from common.database.db_manager import get_db_manager

    db = get_db_manager()
    with db.atomic():
        repository.save(...)
    db.on_commit(lambda: notification_service.send(...))
"""
from __future__ import annotations

from typing import Callable, TypeVar

from django.db import connection, transaction

from common.database.interfaces import IDatabaseManager

T = TypeVar("T")


class DatabaseManager(IDatabaseManager):
    """Django ORM-backed implementation of IDatabaseManager."""

    def atomic(self):
        return transaction.atomic()

    def on_commit(self, callback: Callable[[], None]) -> None:
        transaction.on_commit(callback)

    def run_in_transaction(self, func: Callable[[], T]) -> T:
        with self.atomic():
            return func()

    def health_check(self) -> dict[str, bool]:
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"connected": True}
        except Exception:
            return {"connected": False}


# Module-level singleton (inject get_db_manager() in tests with a fake)
_db_manager: DatabaseManager | None = None


def get_db_manager() -> IDatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def set_db_manager(manager: IDatabaseManager | None) -> None:
    """Override for unit tests."""
    global _db_manager
    _db_manager = manager  # type: ignore[assignment]
