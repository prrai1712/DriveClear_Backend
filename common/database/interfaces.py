"""
Database abstractions (Dependency Inversion).

Services and repositories depend on IDatabaseManager, not Django internals directly.
"""
from __future__ import annotations

from typing import Any, Callable, Protocol, TypeVar

T = TypeVar("T")


class IDatabaseManager(Protocol):
    """Contract for transaction and connection management."""

    def atomic(self) -> Any:
        """Return a context manager for a single database transaction."""

    def on_commit(self, callback: Callable[[], None]) -> None:
        """Schedule callback after successful commit."""

    def run_in_transaction(self, func: Callable[[], T]) -> T:
        """Execute callable inside atomic block and return its result."""

    def health_check(self) -> dict[str, bool]:
        """Return database connectivity status."""
