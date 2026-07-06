"""Persistence helpers for messages, logs, settings, snapshots, power events."""
import json
from datetime import datetime, timedelta, timezone

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


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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


def set_message_protected(mid: int, protected: bool) -> bool:
    cur = db.write(
        "UPDATE messages SET protected=? WHERE id=?",
        (int(bool(protected)), mid))
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


# --- retention ---------------------------------------------------------------

RETENTION_INTERVAL_DAYS = 7
DETAIL_RETENTION_DAYS = 30
MESSAGE_RETENTION_DAYS = 90
SUMMARY_RETENTION_DAYS = 180
SNAPSHOT_RETENTION_DAYS = 30
DEFAULT_DB_TARGET_MB = 25


def database_status() -> dict:
    target_mb = _int_setting("database_target_mb", DEFAULT_DB_TARGET_MB)
    size = db.size_bytes()
    target_bytes = max(1, target_mb) * 1024 * 1024
    return {
        "path": str(db.path()),
        "size_bytes": size,
        "size_mb": round(size / (1024 * 1024), 2),
        "target_mb": target_mb,
        "target_bytes": target_bytes,
        "percent": min(100, round(size * 100 / target_bytes)) if target_bytes else 0,
        "over_target": size >= target_bytes,
    }


def _int_setting(key: str, default: int) -> int:
    try:
        return int(get_setting(key, str(default)))
    except (TypeError, ValueError):
        return default


def maintenance_status(now_dt: datetime | None = None) -> dict:
    now_dt = (now_dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    last = get_setting("database_maintenance_last_at")
    last_dt = _parse_ts(last)
    next_dt = (last_dt + timedelta(days=RETENTION_INTERVAL_DAYS)) if last_dt else None
    due = last_dt is None or now_dt >= next_dt
    return {
        "last_at": last,
        "next_at": _iso(next_dt) if next_dt else "on next service loop",
        "due": due,
        "interval_days": RETENTION_INTERVAL_DAYS,
        "detail_days": DETAIL_RETENTION_DAYS,
        "message_days": MESSAGE_RETENTION_DAYS,
        "summary_days": SUMMARY_RETENTION_DAYS,
        "snapshot_days": SNAPSHOT_RETENTION_DAYS,
    }


def run_database_maintenance(now_dt: datetime | None = None, force: bool = False) -> dict:
    """Compact old duplicate operational records and prune stale detail rows.

    This intentionally leaves tokens and pinned messages alone. The goal is to
    keep noisy Pi conditions, especially repeated power warnings, from growing
    SQLite indefinitely while preserving recent detail and long-term summaries.
    """
    now_dt = (now_dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    status = maintenance_status(now_dt)
    if not force and not status["due"]:
        return {"ok": True, "skipped": True, **status}

    weekly_cutoff = _iso(now_dt - timedelta(days=RETENTION_INTERVAL_DAYS))
    detail_cutoff = _iso(now_dt - timedelta(days=DETAIL_RETENTION_DAYS))
    message_cutoff = _iso(now_dt - timedelta(days=MESSAGE_RETENTION_DAYS))
    summary_cutoff = _iso(now_dt - timedelta(days=SUMMARY_RETENTION_DAYS))
    snapshot_cutoff = _iso(now_dt - timedelta(days=SNAPSHOT_RETENTION_DAYS))

    stats = {
        "ok": True,
        "skipped": False,
        "log_summaries": _summarize_logs(weekly_cutoff),
        "message_summaries": _summarize_messages(weekly_cutoff),
        "power_summaries": _summarize_power_events(weekly_cutoff),
        "logs_deleted": _delete_old_logs(detail_cutoff, summary_cutoff),
        "messages_deleted": _delete_old_messages(message_cutoff, summary_cutoff),
        "power_events_deleted": _delete_old_power_events(message_cutoff),
        "snapshots_deleted": _delete_old_snapshots(snapshot_cutoff),
    }
    deleted = (stats["logs_deleted"] + stats["messages_deleted"] +
               stats["power_events_deleted"] + stats["snapshots_deleted"])
    db.maintenance(deleted)
    set_setting("database_maintenance_last_at", _iso(now_dt))
    log("info", "retention", "database_maintenance",
        " ".join(f"{k}={v}" for k, v in stats.items() if k not in ("ok", "skipped")))
    return {**stats, **maintenance_status(now_dt)}


def _delete_ids(table: str, ids: list[int]) -> int:
    deleted = 0
    for i in range(0, len(ids), 250):
        chunk = ids[i:i + 250]
        placeholders = ",".join("?" for _ in chunk)
        cur = db.write(f"DELETE FROM {table} WHERE id IN ({placeholders})", tuple(chunk))
        deleted += cur.rowcount
    return deleted


def _summarize_logs(cutoff: str) -> int:
    rows = db.query(
        "SELECT id, level, source, event, detail, created_at FROM logs "
        "WHERE created_at < ? AND source != 'retention'",
        (cutoff,))
    groups: dict[tuple, list] = {}
    for r in rows:
        groups.setdefault((r["level"], r["source"], r["event"], r["detail"]), []).append(r)

    summaries = 0
    for (level, source, event, detail), items in groups.items():
        if len(items) < 2:
            continue
        items = sorted(items, key=lambda r: r["created_at"])
        detail_txt = (detail or "").replace("\n", " ")[:180]
        summary = (f"{len(items)} matching logs from {items[0]['created_at']} "
                   f"to {items[-1]['created_at']}; level={level} source={source} "
                   f"event={event}" + (f" detail={detail_txt}" if detail_txt else ""))
        db.write(
            "INSERT INTO logs (level, source, event, detail, created_at) "
            "VALUES (?,?,?,?,?)",
            ("info", "retention", "log_summary", summary, items[-1]["created_at"]))
        _delete_ids("logs", [r["id"] for r in items])
        summaries += 1
    return summaries


def _summarize_messages(cutoff: str) -> int:
    rows = db.query(
        "SELECT * FROM messages WHERE created_at < ? AND pinned=0 AND protected=0 "
        "AND source != 'retention'",
        (cutoff,))
    groups: dict[tuple, list] = {}
    for r in rows:
        key = (r["source"], r["type"], r["category"], r["title"], r["message"],
               r["status"], r["metadata_json"])
        groups.setdefault(key, []).append(r)

    summaries = 0
    for key, items in groups.items():
        if len(items) < 2:
            continue
        source, type_, category, title, message, status, metadata_json = key
        items = sorted(items, key=lambda r: r["created_at"])
        summary_meta = {
            "count": len(items),
            "source": source,
            "type": type_,
            "category": category,
            "status": status,
            "first": items[0]["created_at"],
            "last": items[-1]["created_at"],
        }
        summary_title = f"{len(items)}x {title}"[:48]
        summary_msg = (f"Collapsed matching unpinned messages from "
                       f"{items[0]['created_at']} to {items[-1]['created_at']}.")
        if message:
            summary_msg = f"{summary_msg} Last detail: {message[:220]}"
        db.write(
            """INSERT INTO messages
               (source, type, category, title, message, pinned, priority, status,
                metadata_json, created_at, cleared_at)
               VALUES (?,?,?,?,?,0,1,'cleared',?,?,?)""",
            ("retention", "note", "summary", summary_title, summary_msg,
             json.dumps(summary_meta), items[-1]["created_at"], items[-1]["created_at"]))
        _delete_ids("messages", [r["id"] for r in items])
        summaries += 1
    return summaries


def _summarize_power_events(cutoff: str) -> int:
    rows = db.query(
        "SELECT * FROM power_events WHERE created_at < ?",
        (cutoff,))
    groups: dict[tuple, list] = {}
    for r in rows:
        key = (r["raw_value"], r["undervoltage_now"], r["undervoltage_occurred"],
               r["throttled_now"], r["throttled_occurred"],
               r["frequency_capped_now"], r["frequency_capped_occurred"])
        groups.setdefault(key, []).append(r)

    summaries = 0
    for key, items in groups.items():
        if len(items) < 2:
            continue
        items = sorted(items, key=lambda r: r["created_at"])
        detail = (f"{len(items)} matching power events from {items[0]['created_at']} "
                  f"to {items[-1]['created_at']}; raw={key[0]}")
        db.write(
            "INSERT INTO logs (level, source, event, detail, created_at) "
            "VALUES (?,?,?,?,?)",
            ("info", "retention", "power_event_summary", detail, items[-1]["created_at"]))
        _delete_ids("power_events", [r["id"] for r in items])
        summaries += 1
    return summaries


def _delete_old_logs(detail_cutoff: str, summary_cutoff: str) -> int:
    cur = db.write(
        "DELETE FROM logs WHERE (source != 'retention' AND created_at < ?) "
        "OR (source = 'retention' AND created_at < ?)",
        (detail_cutoff, summary_cutoff))
    return cur.rowcount


def _delete_old_messages(message_cutoff: str, summary_cutoff: str) -> int:
    cur = db.write(
        "DELETE FROM messages WHERE pinned=0 AND protected=0 AND "
        "((source != 'retention' AND status='cleared' AND created_at < ?) "
        "OR (source = 'retention' AND created_at < ?))",
        (message_cutoff, summary_cutoff))
    return cur.rowcount


def _delete_old_power_events(cutoff: str) -> int:
    cur = db.write("DELETE FROM power_events WHERE created_at < ?", (cutoff,))
    return cur.rowcount


def _delete_old_snapshots(cutoff: str) -> int:
    cur = db.write("DELETE FROM system_snapshots WHERE created_at < ?", (cutoff,))
    return cur.rowcount


def cleanup_logs_keep_days(days: int = DETAIL_RETENTION_DAYS,
                           now_dt: datetime | None = None) -> int:
    now_dt = (now_dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = _iso(now_dt - timedelta(days=days))
    cur = db.write("DELETE FROM logs WHERE created_at < ?", (cutoff,))
    db.maintenance(cur.rowcount)
    log("info", "admin", "logs_cleanup", f"keep_days={days} deleted={cur.rowcount}")
    return cur.rowcount


def cleanup_messages_keep_days(days: int = DETAIL_RETENTION_DAYS,
                               now_dt: datetime | None = None) -> int:
    now_dt = (now_dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = _iso(now_dt - timedelta(days=days))
    cur = db.write(
        "DELETE FROM messages WHERE pinned=0 AND protected=0 "
        "AND status='cleared' AND created_at < ?",
        (cutoff,))
    db.maintenance(cur.rowcount)
    log("info", "admin", "messages_cleanup", f"keep_days={days} deleted={cur.rowcount}")
    return cur.rowcount
