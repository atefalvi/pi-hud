# Database Schema

Use SQLite with WAL mode.

## Pragmas

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
```

## messages

```sql
CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  type TEXT NOT NULL,
  category TEXT,
  title TEXT NOT NULL,
  message TEXT,
  pinned INTEGER NOT NULL DEFAULT 0,
  priority INTEGER NOT NULL DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'active',
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  acknowledged_at TEXT,
  cleared_at TEXT,
  displayed_at TEXT
);
```

## app_tokens

```sql
CREATE TABLE app_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  token_prefix TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  permissions_json TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  last_used_at TEXT,
  revoked_at TEXT
);
```

## logs

```sql
CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  source TEXT NOT NULL,
  event TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
```

## system_snapshots

```sql
CREATE TABLE system_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cpu_percent REAL,
  ram_percent REAL,
  temp_c REAL,
  disk_percent REAL,
  api_status TEXT,
  display_status TEXT,
  db_status TEXT,
  created_at TEXT NOT NULL
);
```

## power_events

```sql
CREATE TABLE power_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  raw_value TEXT NOT NULL,
  undervoltage_now INTEGER NOT NULL DEFAULT 0,
  undervoltage_occurred INTEGER NOT NULL DEFAULT 0,
  throttled_now INTEGER NOT NULL DEFAULT 0,
  throttled_occurred INTEGER NOT NULL DEFAULT 0,
  frequency_capped_now INTEGER NOT NULL DEFAULT 0,
  frequency_capped_occurred INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
```

## settings

```sql
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## active message selection

Current display message:

```sql
SELECT *
FROM messages
WHERE status = 'active'
ORDER BY priority DESC, created_at ASC
LIMIT 1;
```

Queue summary groups:

```sql
SELECT category, type, COUNT(*) AS count
FROM messages
WHERE status = 'active'
GROUP BY category, type
ORDER BY MAX(priority) DESC;
```
