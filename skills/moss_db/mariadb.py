"""MariaDB connection wrapper, result object, transactions, parameterised queries."""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

import pymysql
from pymysql.cursors import Cursor, DictCursor

from .utils import get_mariadb_config, log_query, retry_once


@dataclass
class MariaDBResult:
    rows: list = field(default_factory=list)
    last_id: int | None = None
    rowcount: int = 0

    def fetchall(self) -> list:
        return self.rows

    def fetchone(self) -> Any | None:
        return self.rows[0] if self.rows else None


@dataclass
class MongoResult:
    """Symmetry dataclass for mongo results (when using convenience wrappers)."""
    docs: list = field(default_factory=list)
    inserted_id: Any = None
    modified_count: int = 0
    deleted_count: int = 0


class MariaDBConn:
    """Context-friendly wrapper around a pymysql connection.

    Usage inside manager:
        with db.mariadb() as conn:
            res = conn.execute("SELECT ...", (42,))
            ...
    """

    def __init__(self, conn: pymysql.connections.Connection) -> None:
        self._conn = conn
        self._in_tx = False

    def execute(
        self,
        sql: str,
        params: tuple | list | dict | None = None,
        *,
        as_dict: bool = False,
    ) -> MariaDBResult:
        """Run parameterised query. Always use params to avoid injection."""
        cur: Cursor | DictCursor
        cursor_cls = DictCursor if as_dict else Cursor
        cur = self._conn.cursor(cursor_cls)
        try:
            p = params if params is not None else None
            log_query("mariadb", sql, p)
            cur.execute(sql, p)
            if cur.description:
                rows = cur.fetchall()
            else:
                rows = []
            last = cur.lastrowid
            rc = cur.rowcount
            # Increment manager stats if attached (simple)
            try:
                if hasattr(self, "_manager") and self._manager:
                    self._manager._inc_query("mariadb")
            except Exception:
                pass
            return MariaDBResult(rows=rows or [], last_id=last, rowcount=rc or 0)
        finally:
            cur.close()

    def executemany(self, sql: str, seq_of_params: list[tuple | dict]) -> MariaDBResult:
        cur = self._conn.cursor()
        try:
            log_query("mariadb", f"executemany: {sql}", f"{len(seq_of_params)} rows")
            cur.executemany(sql, seq_of_params)
            return MariaDBResult(rows=[], last_id=cur.lastrowid, rowcount=cur.rowcount or 0)
        finally:
            cur.close()

    @contextmanager
    def transaction(self) -> Iterator[MariaDBConn]:
        """Explicit transaction block: with conn.transaction(): ..."""
        if self._in_tx:
            raise RuntimeError("Nested transactions not supported")
        self._conn.begin()
        self._in_tx = True
        try:
            yield self
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            self._in_tx = False

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


def _connect_mariadb(config: dict[str, Any] | None = None) -> pymysql.connections.Connection:
    cfg = config or get_mariadb_config()
    conn = pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=Cursor,
        autocommit=True,  # default outside explicit tx
        connect_timeout=5,
    )
    return conn


def connect_mariadb(config: dict[str, Any] | None = None) -> pymysql.connections.Connection:
    """Public connect with exactly one retry on transient errors."""
    cfg = config or get_mariadb_config()
    return retry_once(_connect_mariadb, cfg)
