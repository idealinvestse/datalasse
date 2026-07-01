-- Test migration (idempotent via tracking table)
CREATE TABLE IF NOT EXISTS _test_migration_marker (
    id INT PRIMARY KEY,
    note VARCHAR(64)
);
INSERT IGNORE INTO _test_migration_marker (id, note) VALUES (1, 'applied');
