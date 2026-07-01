"""moss-db: Unified Python wrapper + CLI for MariaDB (ACID SQL) and MongoDB (documents).

Exposes DatabaseManager for connection management, context-managed CRUD,
health checks, migrations, transactions and bulk ops.

Usage (from workspace root):
    PYTHONPATH=skills python3 -c 'from moss_db import DatabaseManager; ...'
    # or inside bin/ and tests (they auto-insert the path):
    from moss_db import DatabaseManager
"""
from __future__ import annotations

__version__ = "0.1.0"

from .manager import DatabaseManager
from .mariadb import MariaDBConn, MariaDBResult, MongoResult
from .mongodb import sanitize_mongo_query
from .utils import load_credentials

# Aliases to match documented import style
MariaDB = MariaDBConn
MongoDB = None  # Primary usage is via DatabaseManager().mongodb(...)

__all__ = [
    "DatabaseManager",
    "MariaDB",
    "MariaDBConn",
    "MariaDBResult",
    "MongoResult",
    "MongoDB",
    "sanitize_mongo_query",
    "load_credentials",
    "__version__",
]
