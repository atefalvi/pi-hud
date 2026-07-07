"""SQLite access. One shared connection (single-worker service) with a write
lock, WAL mode, and idempotent schema creation."""
import sqlite3
import threading
from pathlib import Path

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()
_path: Path | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  type TEXT NOT NULL,
  category TEXT,
  title TEXT NOT NULL,
  message TEXT,
  pinned INTEGER NOT NULL DEFAULT 0,
  protected INTEGER NOT NULL DEFAULT 0,
  priority INTEGER NOT NULL DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'active',
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  acknowledged_at TEXT,
  cleared_at TEXT,
  displayed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status, priority DESC, created_at ASC);

CREATE TABLE IF NOT EXISTS app_tokens (
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

CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  source TEXT NOT NULL,
  event TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at DESC);

CREATE TABLE IF NOT EXISTS system_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cpu_percent REAL, ram_percent REAL, temp_c REAL, disk_percent REAL,
  api_status TEXT, display_status TEXT, db_status TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS power_events (
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
CREATE INDEX IF NOT EXISTS idx_power_created ON power_events(created_at DESC);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def init(path: str) -> sqlite3.Connection:
    global _conn, _path
    _path = Path(path)
    _path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    _conn = conn
    return conn


def _migrate(conn: sqlite3.Connection):
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(messages)").fetchall()}
    if "protected" not in cols:
        conn.execute("ALTER TABLE messages ADD COLUMN protected INTEGER NOT NULL DEFAULT 0")


def conn() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("db.init() not called")
    return _conn


def write(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Run a write under the lock and commit. Returns the cursor."""
    with _lock:
        cur = _conn.execute(sql, params)
        _conn.commit()
        return cur


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return _conn.execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return _conn.execute(sql, params).fetchone()


def path() -> Path:
    if _path is None:
        raise RuntimeError("db.init() not called")
    return _path


def size_bytes() -> int:
    p = path()
    total = p.stat().st_size if p.exists() else 0
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(p) + suffix)
        if sidecar.exists():
            total += sidecar.stat().st_size
    return total


def maintenance(deleted_rows: int = 0):
    """Best-effort SQLite upkeep after periodic retention cleanup."""
    with _lock:
        _conn.execute("PRAGMA optimize;")
        if deleted_rows > 0:
            _conn.execute("VACUUM;")
        _conn.commit()
        _conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")


def checkpoint():
    with _lock:
        _conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
