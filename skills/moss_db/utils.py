"""Utilities for moss-db: credential loading, query logging, retry, mongo sanitiser."""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

MOSS_DIR = Path.home() / ".moss"
QUERY_LOG = MOSS_DIR / "db-query.log"
DEFAULT_MARIADB = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "moss_main",
    "user": "moss",
    "password": "",
}
DEFAULT_MONGODB = {
    "host": "127.0.0.1",
    "port": 27017,
    "database": "moss_data",
    "user": "",
    "password": "",
}


def _ensure_log_dir() -> None:
    MOSS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        MOSS_DIR.chmod(0o700)
    except PermissionError:
        pass


def load_credentials() -> dict[str, str]:
    """Load ~/.moss/db-credentials.env (if present) + allow env overrides."""
    env_path = MOSS_DIR / "db-credentials.env"
    creds: dict[str, str] = {}
    if env_path.exists():
        try:
            loaded = dotenv_values(str(env_path))
            creds = {k: (v or "") for k, v in loaded.items() if v is not None}
        except Exception:
            # fall through to defaults + env
            creds = {}
    # Env overrides (MOSS_* take precedence)
    for k, v in os.environ.items():
        if k.startswith("MOSS_"):
            creds[k] = v
    return creds


def get_mariadb_config(creds: dict[str, str] | None = None) -> dict[str, Any]:
    c = creds or load_credentials()
    return {
        "host": c.get("MOSS_MARIADB_HOST", DEFAULT_MARIADB["host"]),
        "port": int(c.get("MOSS_MARIADB_PORT", DEFAULT_MARIADB["port"])),
        "database": c.get("MOSS_MARIADB_DATABASE", DEFAULT_MARIADB["database"]),
        "user": c.get("MOSS_MARIADB_USER", DEFAULT_MARIADB["user"]),
        "password": c.get("MOSS_MARIADB_PASSWORD", DEFAULT_MARIADB["password"]),
    }


def get_mongodb_config(creds: dict[str, str] | None = None) -> dict[str, Any]:
    c = creds or load_credentials()
    return {
        "host": c.get("MOSS_MONGODB_HOST", DEFAULT_MONGODB["host"]),
        "port": int(c.get("MOSS_MONGODB_PORT", DEFAULT_MONGODB["port"])),
        "database": c.get("MOSS_MONGODB_DATABASE", DEFAULT_MONGODB["database"]),
        "user": c.get("MOSS_MONGODB_USER", DEFAULT_MONGODB["user"]),
        "password": c.get("MOSS_MONGODB_PASSWORD", DEFAULT_MONGODB["password"]),
    }


# Query logger (always appends, level debug in message)
_logger = logging.getLogger("moss_db")
_logger.setLevel(logging.DEBUG)
_handler = None


def _get_logger() -> logging.Logger:
    global _handler
    if _handler is None:
        _ensure_log_dir()
        _handler = logging.FileHandler(str(QUERY_LOG), encoding="utf-8")
        _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        _logger.addHandler(_handler)
        _logger.propagate = False
    return _logger


def log_query(dbtype: str, op: str, params: Any = None) -> None:
    """Log a query/op to ~/.moss/db-query.log. Never logs secrets."""
    _get_logger().debug(f"[{dbtype}] {op} params={_redact_params(params)}")
    # Also direct append for robustness
    try:
        _ensure_log_dir()
        ts = datetime.now(timezone.utc).isoformat()
        line = f"{ts} [{dbtype}] {op} params={_redact_params(params)}\n"
        with open(QUERY_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass  # logging must never break DB ops


def _redact_params(params: Any) -> str:
    if params is None:
        return "None"
    try:
        s = json.dumps(params, default=str)
        if any(x in s.lower() for x in ("password", "passwd", "secret", "token")):
            return "[REDACTED]"
        return s[:500]
    except Exception:
        return str(params)[:200]


def retry_once(func, *args, **kwargs):
    """Run func once, retry exactly once on transient connection errors."""
    try:
        return func(*args, **kwargs)
    except Exception as exc:  # broad - we classify below
        if not _is_transient(exc):
            raise
        time.sleep(0.2)
        return func(*args, **kwargs)


def _is_transient(exc: Exception) -> bool:
    msg = str(exc).lower()
    transient = (
        "timeout",
        "timed out",
        "connection reset",
        "connection refused",
        "connection aborted",
        "broken pipe",
        "operationalerror",
        "network",
        "server has gone away",
        "lost connection",
    )
    return any(t in msg for t in transient)


def sanitize_mongo_query(q: dict | list | None) -> dict | list | None:
    """Remove / block dangerous mongo operators that can execute JS ($where etc)."""
    if q is None:
        return None
    forbidden = {"$where", "$function", "$accumulator", "$code", "$eval"}
    if isinstance(q, list):
        return [sanitize_mongo_query(x) if isinstance(x, (dict, list)) else x for x in q]
    if not isinstance(q, dict):
        return q
    out = {}
    for k, v in q.items():
        if k in forbidden:
            raise ValueError(f"Unsafe MongoDB operator blocked: {k}")
        if isinstance(v, (dict, list)):
            out[k] = sanitize_mongo_query(v)
        else:
            out[k] = v
    return out
