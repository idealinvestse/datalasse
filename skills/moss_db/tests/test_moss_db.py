"""Comprehensive tests for moss_db (minimum 7 + extras).

Run: python3 -m pytest skills/moss_db/tests/ -v
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

# Make imports work
WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / "skills"))

from moss_db import DatabaseManager, sanitize_mongo_query  # noqa: E402
from moss_db.mariadb import MariaDBResult

db = DatabaseManager.from_env()


def _cleanup():
    """Best-effort cleanup of test artifacts."""
    try:
        with db.mariadb() as conn:
            for t in ("_test", "_test_migration_marker", "_test_tx"):
                try:
                    conn.execute(f"DROP TABLE IF EXISTS {t}")
                except Exception:
                    pass
            # Reset migration tracking for test migrations to keep idempotent test reliable
            try:
                conn.execute("DELETE FROM _migrations WHERE name LIKE '%%test%%' OR name LIKE '%%001_test%%'")
            except Exception:
                pass
    except Exception:
        pass
    try:
        with db.mongodb("_test_coll") as coll:
            coll.delete_many({})
        with db.mongodb("_test_tx") as coll:
            coll.delete_many({})
        with db.mongodb("_test_cli") as coll:
            coll.delete_many({})
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _auto_cleanup():
    _cleanup()
    yield
    _cleanup()


def test_mariadb_roundtrip():
    """Test 1: create/insert/select/drop roundtrip."""
    with db.mariadb() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS _test (id INT PRIMARY KEY, name VARCHAR(50))")
        res = conn.execute("INSERT INTO _test (id, name) VALUES (%s, %s)", (1, "alice"))
        assert res.last_id is None or isinstance(res.last_id, int)
        rows = conn.execute("SELECT * FROM _test WHERE id=%s", (1,)).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1 or rows[0] == (1, "alice") or dict(rows[0]).get("id") == 1
        conn.execute("DROP TABLE _test")


def test_mongodb_roundtrip():
    """Test 2: insert / find / update / delete."""
    with db.mongodb("_test_coll") as coll:
        r = coll.insert_one({"name": "bob", "tags": ["x", "y"]})
        assert r.inserted_id is not None
        docs = list(coll.find({"tags": "x"}))
        assert len(docs) >= 1
        coll.update_one({"name": "bob"}, {"$set": {"name": "bobby"}})
        d2 = coll.find_one({"name": "bobby"})
        assert d2 is not None
        coll.delete_many({"name": "bobby"})
        assert coll.count_documents({"name": "bobby"}) == 0


def test_health_reports_up():
    """Test 3: both databases report up."""
    h = db.health()
    assert h["mariadb"]["status"] == "up"
    assert h["mongodb"]["status"] == "up"
    assert "latency_ms" in h["mariadb"]
    assert "latency_ms" in h["mongodb"]


def test_concurrent_queries_no_deadlock():
    """Test 4: 10 concurrent operations work."""
    def do_one(i: int):
        with db.mariadb() as conn:
            conn.execute("SELECT %s", (i,))
        with db.mongodb("_test_coll") as coll:
            coll.insert_one({"i": i})
            coll.delete_one({"i": i})
        return i

    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(do_one, range(10)))
    assert len(results) == 10


def test_context_manager_rollback():
    """Test 5: exception inside with rolls back."""
    with db.mariadb() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS _test_tx (id INT PRIMARY KEY)")
        conn.execute("INSERT INTO _test_tx (id) VALUES (42)")

    # Now use tx + exception
    try:
        with db.mariadb() as conn:
            with conn.transaction():
                conn.execute("INSERT INTO _test_tx (id) VALUES (99)")
                raise RuntimeError("boom")
    except RuntimeError:
        pass

    # 99 must not exist
    with db.mariadb() as conn:
        rows = conn.execute("SELECT id FROM _test_tx").fetchall()
        ids = [r[0] if not isinstance(r, dict) else r.get("id") for r in rows]
        assert 99 not in ids
        conn.execute("DROP TABLE _test_tx")


def test_migration_idempotent():
    """Test 6: running migration twice is safe (idempotent)."""
    # First run
    res1 = db.migrate("moss_main", "001_test_migration")
    assert res1["name"] == "001_test_migration"
    # Second run must skip or succeed without error/dupe side effects
    res2 = db.migrate("moss_main", "001_test_migration")
    assert res2["name"] == "001_test_migration"
    # Verify marker row exists only once
    with db.mariadb() as conn:
        rows = conn.execute("SELECT COUNT(*) FROM _test_migration_marker").fetchall()
        count = rows[0][0] if rows and not isinstance(rows[0], dict) else list(rows[0].values())[0]
        assert count == 1


def test_bad_credentials_clean_error():
    """Test 7: bad credentials give clean error (no raw stack in normal path)."""
    bad = DatabaseManager({
        "MOSS_MARIADB_HOST": "127.0.0.1",
        "MOSS_MARIADB_PORT": "3306",
        "MOSS_MARIADB_DATABASE": "moss_main",
        "MOSS_MARIADB_USER": "no_such_user_zzz",
        "MOSS_MARIADB_PASSWORD": "wrong",
        "MOSS_MONGODB_HOST": "127.0.0.1",
        "MOSS_MONGODB_PORT": "27017",
        "MOSS_MONGODB_DATABASE": "moss_data",
    })
    # Should raise but message should be clear
    with pytest.raises(Exception) as exc:
        with bad.mariadb() as c:
            c.execute("SELECT 1")
    msg = str(exc.value).lower()
    assert any(x in msg for x in ("access denied", "1045", "auth", "password", "user"))


def test_mariadb_result_and_dict_rows():
    with db.mariadb() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS _test (id INT, name TEXT)")
        conn.execute("INSERT INTO _test VALUES (7, 'seven')")
        res = conn.execute("SELECT * FROM _test", as_dict=True)
        assert isinstance(res, MariaDBResult)
        assert res.fetchall()[0]["id"] == 7 or res.fetchall()[0].get("id") == 7
        conn.execute("DROP TABLE _test")


def test_mongo_sanitize_blocks_dangerous():
    with pytest.raises(ValueError):
        sanitize_mongo_query({"$where": "this.a == 1"})
    safe = sanitize_mongo_query({"tags": "x", "nested": {"$in": [1, 2]}})
    assert "$where" not in str(safe)


def test_stats_counters_exist():
    s = db.stats
    assert "mariadb_queries" in s
    assert "mongodb_queries" in s
    assert "errors" in s
