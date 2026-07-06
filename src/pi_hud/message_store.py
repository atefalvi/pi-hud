"""Persistence helpers for messages, logs, settings, snapshots, power events."""
import json
from datetime import datetime, timezone

from . import db

VALID_TYPES = ("success", "info", "note", "warning", "caution", "error", "critical")

# Which queue group a message type falls into, most severe first. Used by the
# pending-queue HUD screen.
_GROUP = {
    "critical": ("Error alerts", 0),
    "error": ("Error alerts", 0),
    "warning": ("Power alerts", 1),
    "caution": ("Power alerts", 1),
    "info": ("Info alerts", 2),
    "success": ("Info alerts", 2),
    "note": ("Info alerts", 2),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- messages ---------------------------------------------------------------

def create_message(source, type, title, message=None, pinned=False, priority=5,
                   category=None, metadata=None) -> int:
    cur = db.write(
        """INSERT INTO messages
           (source, type, category, title, message, pinned, priority, status,
            metadata_json, created_at)
           VALUES (?,?,?,?,?,?,?, 'active', ?, ?)""",
        (source, type, category, title, message, int(bool(pinned)), priority,
         json.dumps(metadata) if metadata else None, now()),
    )
    return cur.lastrowid


def get_message(mid: int):
    return db.query_one("SELECT * FROM messages WHERE id=?", (mid,))


def list_messages(status="all", limit=50, offset=0):
    if status == "all":
        return db.query(
            "SELECT * FROM messages ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset))
    return db.query(
        "SELECT * FROM messages WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (status, limit, offset))


def active_message():
    """Highest-priority active message, regardless of display pinning."""
    return db.query_one(
        "SELECT * FROM messages WHERE status='active' "
        "ORDER BY priority DESC, created_at ASC LIMIT 1")


def display_message():
    """The single message eligible for the physical display."""
    return db.query_one(
        "SELECT * FROM messages WHERE status='active' AND pinned=1 "
        "ORDER BY priority DESC, created_at ASC LIMIT 1")


def active_count() -> int:
    return db.query_one(
        "SELECT COUNT(*) c FROM messages WHERE status='active'")["c"]


def display_count() -> int:
    return db.query_one(
        "SELECT COUNT(*) c FROM messages WHERE status='active' AND pinned=1")["c"]


def queue_groups():
    """Grouped active-message counts for the pending screen, ordered by
    severity. Returns list of (label, count, group_index)."""
    return _queue_groups("WHERE status='active'")


def display_queue_groups():
    """Grouped display-eligible message counts for the pending screen."""
    return _queue_groups("WHERE status='active' AND pinned=1")


def _queue_groups(where_clause: str):
    rows = db.query(
        f"SELECT type, COUNT(*) c FROM messages {where_clause} GROUP BY type")
    agg: dict[str, int] = {}
    order: dict[str, int] = {}
    for r in rows:
        label, gi = _GROUP.get(r["type"], ("Info alerts", 2))
        agg[label] = agg.get(label, 0) + r["c"]
        order[label] = gi
    return sorted(((lbl, cnt, order[lbl]) for lbl, cnt in agg.items()),
                  key=lambda x: x[2])


def clear_message(mid: int) -> bool:
    cur = db.write(
        "UPDATE messages SET status='cleared', cleared_at=? WHERE id=? AND status='active'",
        (now(), mid))
    return cur.rowcount > 0


def clear_current() -> int | None:
    m = display_message()
    if m and clear_message(m["id"]):
        return m["id"]
    return None


def set_message_pinned(mid: int, pinned: bool) -> bool:
    cur = db.write(
        "UPDATE messages SET pinned=? WHERE id=? AND status='active'",
        (int(bool(pinned)), mid))
    return cur.rowcount > 0


def set_active_category_pinned(category: str, pinned: bool) -> int:
    cur = db.write(
        "UPDATE messages SET pinned=? WHERE status='active' AND category=?",
        (int(bool(pinned)), category))
    return cur.rowcount


def clear_all() -> int:
    cur = db.write(
        "UPDATE messages SET status='cleared', cleared_at=? WHERE status='active'",
        (now(),))
    return cur.rowcount


def mark_displayed(mid: int):
    db.write("UPDATE messages SET displayed_at=? WHERE id=? AND displayed_at IS NULL",
             (now(), mid))


# --- logs -------------------------------------------------------------------

def log(level, source, event, detail=None):
    db.write(
        "INSERT INTO logs (level, source, event, detail, created_at) VALUES (?,?,?,?,?)",
        (level, source, event, detail, now()))


def list_logs(limit=100):
    return db.query("SELECT * FROM logs ORDER BY created_at DESC LIMIT ?", (limit,))


# --- settings (runtime-tunable overrides) -----------------------------------

def get_setting(key: str, default=None):
    r = db.query_one("SELECT value FROM settings WHERE key=?", (key,))
    return r["value"] if r else default


def set_setting(key: str, value: str):
    db.write(
        "INSERT INTO settings (key, value, updated_at) VALUES (?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (key, str(value), now()))


def all_settings() -> dict:
    return {r["key"]: r["value"] for r in db.query("SELECT key, value FROM settings")}


# --- snapshots / power ------------------------------------------------------

def save_snapshot(cpu, ram, temp, disk, api_status, display_status, db_status):
    db.write(
        """INSERT INTO system_snapshots
           (cpu_percent, ram_percent, temp_c, disk_percent,
            api_status, display_status, db_status, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (cpu, ram, temp, disk, api_status, display_status, db_status, now()))


def save_power_event(flags: dict, raw: str):
    db.write(
        """INSERT INTO power_events
           (raw_value, undervoltage_now, undervoltage_occurred, throttled_now,
            throttled_occurred, frequency_capped_now, frequency_capped_occurred, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (raw, flags["undervoltage_now"], flags["undervoltage_occurred"],
         flags["throttled_now"], flags["throttled_occurred"],
         flags["frequency_capped_now"], flags["frequency_capped_occurred"], now()))


def list_power_events(limit=50):
    return db.query("SELECT * FROM power_events ORDER BY created_at DESC LIMIT ?", (limit,))
