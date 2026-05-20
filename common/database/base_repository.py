"""
BaseRepository — shared DB access for all repositories (DRY + DIP).
"""
from __future__ import annotations

from common.database.db_manager import get_db_manager
from common.database.interfaces import IDatabaseManager


class BaseRepository:
    def __init__(self, db: IDatabaseManager | None = None) -> None:
        self._db = db or get_db_manager()
