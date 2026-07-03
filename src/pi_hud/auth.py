"""App token creation, verification, revocation. Only hashes are stored; the
plaintext token is shown once at creation."""
import hashlib
import json
import secrets

from . import db
from .message_store import now

PREFIX_LEN = 11  # "ph_" + 8 hex chars, enough to identify a token in the UI


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_token(name: str, permissions=None) -> tuple[int, str]:
    """Returns (id, plaintext_token). Token is never recoverable afterwards."""
    token = "ph_" + secrets.token_hex(24)
    cur = db.write(
        """INSERT INTO app_tokens
           (name, token_prefix, token_hash, permissions_json, is_active, created_at)
           VALUES (?,?,?,?,1,?)""",
        (name, token[:PREFIX_LEN], _hash(token),
         json.dumps(permissions or ["write"]), now()))
    return cur.lastrowid, token


def verify(token: str | None) -> bool:
    """True if the bearer token maps to an active token. Updates last_used_at."""
    if not token or not token.startswith("ph_"):
        return False
    row = db.query_one(
        "SELECT id FROM app_tokens WHERE token_hash=? AND is_active=1",
        (_hash(token),))
    if row:
        db.write("UPDATE app_tokens SET last_used_at=? WHERE id=?", (now(), row["id"]))
        return True
    return False


def revoke(token_id: int) -> bool:
    cur = db.write(
        "UPDATE app_tokens SET is_active=0, revoked_at=? WHERE id=? AND is_active=1",
        (now(), token_id))
    return cur.rowcount > 0


def list_tokens():
    return db.query("SELECT * FROM app_tokens ORDER BY created_at DESC")


def has_any_active() -> bool:
    return db.query_one(
        "SELECT COUNT(*) c FROM app_tokens WHERE is_active=1")["c"] > 0


def ensure_first_token(name: str = "pi-dns-sync") -> str | None:
    """Create a starter token on a fresh install. Returns the plaintext once,
    or None if a token already exists (idempotent re-runs)."""
    if has_any_active():
        return None
    _, token = create_token(name)
    return token
