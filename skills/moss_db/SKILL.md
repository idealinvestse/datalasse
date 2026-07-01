---
name: moss-db
description: "Unified Python API + CLI wrapper for MariaDB (relational/ACID) and MongoDB (documents). Singleton manager, context managers, health, migrations, tx, bulk, retry, logging."
---

# moss-db

Unified, safe wrapper for both Moss databases:
- **MariaDB 11** (127.0.0.1:3306, `moss_main`, user `moss`) — SQL, transactions, ACID.
- **MongoDB 7** (Docker `moss-mongodb`, 127.0.0.1:27017, `moss_data`, no auth) — documents, flexible.

## Installation (inside workspace)

```bash
pip install pymysql pymongo python-dotenv
```

## Python API (primary)

```python
# From workspace root (recommended):
#   PYTHONPATH=skills python3 -c 'from moss_db import DatabaseManager'
from moss_db import DatabaseManager

db = DatabaseManager.from_env()   # reads ~/.moss/db-credentials.env

# MariaDB
with db.mariadb() as conn:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100))"
    )
    rid = conn.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",)).last_id
    rows = conn.execute("SELECT * FROM users WHERE id = %s", (rid,)).fetchall()

    with conn.transaction():
        conn.execute("UPDATE users SET name=%s WHERE id=%s", ("Bob", rid))

# MongoDB
with db.mongodb("events") as coll:
    coll.insert_one({"type": "login", "user": "alice", "tags": ["x"]})
    docs = coll.find({"tags": "x"}).limit(10).to_list()
    coll.insert_many([...])
    # full power: bulk_write etc.
```

## CLI (bin/moss-db)

```bash
bin/moss-db status
bin/moss-db stats
bin/moss-db mariadb exec "SELECT VERSION()"
bin/moss-db mariadb migrate 001_create_users
bin/moss-db mongodb collections
bin/moss-db mongodb find events --query '{"tags":"x"}' --limit 5
bin/moss-db mongodb insert events --doc '{"type":"test"}'
```

## Migrations

Place files in `skills/moss_db/migrations/<name>.sql` (MariaDB) or `.json` (Mongo).

```bash
bin/moss-db mariadb migrate 001_create_users
```

Migrations are idempotent via `_migrations` table/collection.

## Security

- Always parameterised queries (`%s`).
- Mongo queries are sanitised for `$where` / JS execution in CLI and helpers.
- Credentials file 0600, never committed.
- `status` / `stats` are read-only.

## Logging

Queries logged to `~/.moss/db-query.log`.

## Tests

```bash
python3 -m pytest skills/moss_db/tests/ -v
```

## Verification (full)

See plan.md. Key commands (use PYTHONPATH for clean `from moss_db` imports from workspace root):

```bash
pip install pymysql pymongo python-dotenv
python3 -m pytest skills/moss_db/tests/ -v
bin/moss-db status
PYTHONPATH=skills python3 -c '
from moss_db import DatabaseManager
...
'
```

The bare `python3 -c "from moss_db..."` works after `export PYTHONPATH=skills` or when using the bin/tests (which insert the path).

## Out of scope

See plan.md (no sharding, no ORM, no public exposure, etc.).

## Related

- bin/moss-wallet (future tx log consumer)
- bin/kill-tony, ffmpeg-vision (analytics)
