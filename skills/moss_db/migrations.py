"""Migration runner: load .sql/.json, ensure tracking, idempotent apply."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .mariadb import MariaDBConn, connect_mariadb
from .mongodb import get_mongo_client
from .utils import get_mariadb_config, get_mongodb_config, log_query

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _load_file(name: str) -> tuple[str, str]:
    """Return (content, kind) where kind in ('sql', 'json')."""
    candidates = [
        MIGRATIONS_DIR / f"{name}.sql",
        MIGRATIONS_DIR / f"{name}.json",
        MIGRATIONS_DIR / name,  # allow full name
    ]
    for p in candidates:
        if p.exists():
            content = p.read_text(encoding="utf-8")
            kind = "json" if p.suffix == ".json" else "sql"
            return content, kind
    raise FileNotFoundError(f"Migration not found: {name} (looked in {MIGRATIONS_DIR})")


def ensure_mariadb_migrations_table(conn: MariaDBConn) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS _migrations ("
        "name VARCHAR(255) PRIMARY KEY, "
        "applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
        ")"
    )


def is_mariadb_applied(conn: MariaDBConn, name: str) -> bool:
    res = conn.execute("SELECT 1 FROM _migrations WHERE name = %s", (name,))
    return bool(res.rows)


def mark_mariadb_applied(conn: MariaDBConn, name: str) -> None:
    conn.execute(
        "INSERT IGNORE INTO _migrations (name, applied_at) VALUES (%s, %s)",
        (name, datetime.now(timezone.utc)),
    )


def apply_sql_migration(conn: MariaDBConn, name: str, content: str) -> None:
    # Simple multi-statement support (split on ; not inside strings is hard; use execute per line-ish)
    # Safe approach: run whole as script via cursor, but pymysql does not have executescript.
    # Split on semicolons that are statement terminators.
    statements = [s.strip() for s in content.split(";") if s.strip()]
    for stmt in statements:
        if stmt:
            conn.execute(stmt)


def ensure_mongo_migrations_coll() -> None:
    client = get_mongo_client()
    db = client[get_mongodb_config()["database"]]
    coll = db["_migrations"]
    coll.create_index("name", unique=True)


def is_mongo_applied(name: str) -> bool:
    client = get_mongo_client()
    db = client[get_mongodb_config()["database"]]
    return db["_migrations"].find_one({"name": name}) is not None


def mark_mongo_applied(name: str) -> None:
    client = get_mongo_client()
    db = client[get_mongodb_config()["database"]]
    db["_migrations"].update_one(
        {"name": name},
        {"$set": {"name": name, "applied_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


def apply_json_migration(name: str, content: str) -> None:
    """Very small mongo migration format:
    {"ops": [{"coll": "users", "insert": {"name": "x"}}, ... ]}
    """
    data = json.loads(content)
    client = get_mongo_client()
    db = client[get_mongodb_config()["database"]]
    for op in data.get("ops", []):
        coll = db[op["coll"]]
        if "insert" in op:
            docs = op["insert"]
            if isinstance(docs, dict):
                docs = [docs]
            coll.insert_many(docs)
        elif "insert_many" in op:
            coll.insert_many(op["insert_many"])
        # extend as needed


def apply_migration(db_name: str, name: str) -> dict[str, Any]:
    """Idempotent migration apply. Returns status info."""
    content, kind = _load_file(name)
    result: dict[str, Any] = {"name": name, "kind": kind, "applied": False}

    if kind == "sql":
        # MariaDB path (db_name is advisory)
        cfg = get_mariadb_config()
        raw_conn = connect_mariadb(cfg)
        conn = MariaDBConn(raw_conn)
        try:
            ensure_mariadb_migrations_table(conn)
            if is_mariadb_applied(conn, name):
                result["applied"] = False
                result["skipped"] = "already applied"
                log_query("mariadb", f"migrate skip {name}")
                return result
            apply_sql_migration(conn, name, content)
            mark_mariadb_applied(conn, name)
            result["applied"] = True
            log_query("mariadb", f"migrate applied {name}")
        finally:
            conn.close()
    else:
        # JSON / mongo
        ensure_mongo_migrations_coll()
        if is_mongo_applied(name):
            result["applied"] = False
            result["skipped"] = "already applied"
            return result
        apply_json_migration(name, content)
        mark_mongo_applied(name)
        result["applied"] = True
    return result
