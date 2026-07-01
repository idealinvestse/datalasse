"""MongoDB helpers: lazy client access, sanitiser re-export, context support."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from pymongo import MongoClient

from .utils import get_mongodb_config, sanitize_mongo_query


class _MongoClientHolder:
    """Lazy singleton holder for the MongoClient (pools internally)."""

    _client: MongoClient | None = None

    @classmethod
    def get(cls, config: dict[str, Any] | None = None) -> MongoClient:
        if cls._client is None:
            cfg = config or get_mongodb_config()
            host = cfg["host"]
            port = cfg["port"]
            user = cfg.get("user") or ""
            pw = cfg.get("password") or ""
            if user and pw:
                uri = f"mongodb://{user}:{pw}@{host}:{port}/?authSource=admin"
            else:
                uri = f"mongodb://{host}:{port}/"
            cls._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
                socketTimeoutMS=10000,
            )
            # Force connect / validate
            cls._client.admin.command("ping")
        return cls._client

    @classmethod
    def reset(cls) -> None:
        if cls._client is not None:
            try:
                cls._client.close()
            except Exception:
                pass
            cls._client = None


@contextmanager
def mongo_context(collection: str | None = None) -> Iterator[Any]:
    """Yield either a collection or the database object."""
    client = _MongoClientHolder.get()
    cfg = get_mongodb_config()
    mdb = client[cfg["database"]]
    if collection:
        yield mdb[collection]
    else:
        yield mdb


def get_mongo_client() -> MongoClient:
    return _MongoClientHolder.get()


def ping_mongo() -> float:
    """Return latency in ms for health check."""
    t0 = __import__("time").perf_counter()
    client = get_mongo_client()
    client.admin.command("ping")
    return (__import__("time").perf_counter() - t0) * 1000
