"""DatabaseManager: central entry point with context managers, health, migrate, stats."""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

from .mariadb import MariaDBConn, connect_mariadb, MongoResult  # re-export for symmetry
from .migrations import apply_migration
from .mongodb import _MongoClientHolder, mongo_context, ping_mongo
from .utils import (
    get_mariadb_config,
    get_mongodb_config,
    load_credentials,
    log_query,
)


@dataclass
class _Stats:
    mariadb_queries: int = 0
    mongodb_queries: int = 0
    errors: int = 0
    connections_opened: int = 0


class DatabaseManager:
    """Singleton-style manager. Preferred usage:

    db = DatabaseManager.from_env()
    with db.mariadb() as conn: ...
    with db.mongodb("coll") as coll: ...
    """

    def __init__(self, creds: dict[str, str] | None = None) -> None:
        self._creds = creds or load_credentials()
        self._stats = _Stats()
        self._maria_config = get_mariadb_config(self._creds)
        self._mongo_config = get_mongodb_config(self._creds)

    @classmethod
    def from_env(cls) -> "DatabaseManager":
        return cls()

    # --- contexts ---

    @contextmanager
    def mariadb(self) -> Iterator[MariaDBConn]:
        self._stats.connections_opened += 1
        conn = None
        try:
            raw = connect_mariadb(self._maria_config)
            conn = MariaDBConn(raw)
            # attach for stats inc
            try:
                conn._manager = self
            except Exception:
                pass
            yield conn
        except Exception:
            self._stats.errors += 1
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            if conn is not None:
                conn.close()

    @contextmanager
    def mongodb(self, collection: str | None = None) -> Iterator[Any]:
        try:
            with mongo_context(collection) as coll:
                self._inc_query("mongodb")  # count entry into mongo ctx as activity
                yield coll
        except Exception:
            self._stats.errors += 1
            raise

    # --- health ---

    def health(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        # MariaDB
        t0 = time.perf_counter()
        try:
            with self.mariadb() as conn:
                conn.execute("SELECT 1")
            latency = (time.perf_counter() - t0) * 1000
            out["mariadb"] = {"status": "up", "latency_ms": round(latency, 1)}
        except Exception as e:
            out["mariadb"] = {"status": "down", "error": str(e)[:120]}

        # MongoDB
        t0 = time.perf_counter()
        try:
            lat = ping_mongo()
            out["mongodb"] = {"status": "up", "latency_ms": round(lat, 1)}
        except Exception as e:
            out["mongodb"] = {"status": "down", "error": str(e)[:120]}
        return out

    # --- migrate ---

    def migrate(self, db_name: str, migration_name: str) -> dict[str, Any]:
        return apply_migration(db_name, migration_name)

    # --- stats ---

    @property
    def stats(self) -> dict[str, Any]:
        # Also attach live mongo client info if possible
        mongo_info: dict[str, Any] = {}
        try:
            client = _MongoClientHolder.get()
            mongo_info = {"pooled": True}
        except Exception:
            pass
        return {
            "mariadb_queries": self._stats.mariadb_queries,
            "mongodb_queries": self._stats.mongodb_queries,
            "errors": self._stats.errors,
            "connections_opened": self._stats.connections_opened,
            "mongo": mongo_info,
        }

    # Internal counters (used by wrappers if they call back; simple inc exposed)
    def _inc_query(self, dbtype: str) -> None:
        if dbtype == "mariadb":
            self._stats.mariadb_queries += 1
        else:
            self._stats.mongodb_queries += 1
