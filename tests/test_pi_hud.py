"""pi-hud test suite. Covers config, store, auth, power parsing, renderer,
and the HTTP API. Uses a temp SQLite DB and a headless display."""
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pi_hud import auth, config, db, power, renderer  # noqa: E402
from pi_hud import message_store as store  # noqa: E402
from pi_hud.api import create_app  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    c = config.load("config.example.ini")
    c._p.set("database", "path", tempfile.mktemp(suffix=".db"))
    c._p.set("display", "enabled", "false")
    db.init(c.get("database", "path"))
    return c


class _Loop:
    status = "unavailable"


@pytest.fixture(scope="module")
def client(cfg):
    return TestClient(create_app(cfg, _Loop()))


# --- config ---
def test_config_defaults():
    c = config.load("does-not-exist.ini")
    assert c.getint("api", "port") == 8765
    assert c.get("api", "host") == "127.0.0.1"


# --- store / selection / grouping ---
def test_active_selection_by_priority(cfg):
    store.clear_all()
    store.create_message("a", "info", "low", priority=2)
    hi = store.create_message("a", "error", "high", priority=9)
    assert store.active_message()["id"] == hi


def test_queue_grouping(cfg):
    store.clear_all()
    store.create_message("a", "error", "e1")
    store.create_message("a", "critical", "e2")
    store.create_message("a", "caution", "p1")
    store.create_message("a", "info", "i1")
    groups = dict((g[0], g[1]) for g in store.queue_groups())
    assert groups["Error alerts"] == 2
    assert groups["Power alerts"] == 1
    assert groups["Info alerts"] == 1
    # most severe first
    assert store.queue_groups()[0][0] == "Error alerts"


def test_clear_current(cfg):
    store.clear_all()
    mid = store.create_message("a", "info", "t")
    assert store.clear_current() == mid
    assert store.active_count() == 0


# --- auth ---
def test_token_lifecycle(cfg):
    tid, tok = auth.create_token("app-" + os.urandom(3).hex())
    assert tok.startswith("ph_")
    assert auth.verify(tok)
    assert not auth.verify("ph_bogus")
    assert not auth.verify(None)
    assert auth.revoke(tid)
    assert not auth.verify(tok)  # revoked


def test_token_hash_not_plaintext(cfg):
    _, tok = auth.create_token("app-" + os.urandom(3).hex())
    rows = auth.list_tokens()
    assert all(tok not in (r["token_hash"] or "") for r in rows)


# --- power parsing ---
def test_power_parse():
    f = power.parse("throttled=0x50005")
    assert f["undervoltage_now"] == 1
    assert f["throttled_now"] == 1
    assert f["undervoltage_occurred"] == 1
    assert f["throttled_occurred"] == 1
    assert power.is_active(f)
    clean = power.parse("throttled=0x0")
    assert not power.has_warning(clean)


# --- renderer ---
def test_renderer_clamps_long_title(cfg):
    img = renderer.render_alert("error", "X" * 200, "body", True, "src")
    assert img.size == (160, 80)


def test_renderer_screens():
    assert renderer.render_normal(
        {"hostname": "pi", "cpu_percent": 10, "ram_percent": 20, "temp_c": 40},
        [("DNS", renderer.SUCCESS)], {"temp": renderer.SUCCESS,
        "cpu": renderer.SUCCESS, "ram": renderer.SUCCESS}).size == (160, 80)
    assert renderer.render_queue(3, [("Error alerts", 1, renderer.DANGER)]).size == (160, 80)


# --- API ---
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_requires_token(client):
    r = client.post("/api/v1/messages", json={"source": "x", "type": "info", "title": "t"})
    assert r.status_code == 401


def test_create_with_token(client, cfg):
    _, tok = auth.create_token("api-" + os.urandom(3).hex())
    r = client.post("/api/v1/messages",
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"source": "pi-dns-sync", "type": "success",
                          "title": "DNS Updated", "pinned": True, "category": "dns",
                          "metadata": {"host": "h", "record_type": "A",
                                       "previous_value": "1.1.1.1",
                                       "updated_value": "2.2.2.2"}})
    assert r.status_code == 200
    mid = r.json()["message_id"]
    detail = client.get(f"/api/v1/messages/{mid}").json()
    assert detail["metadata_json"]
    assert client.post(f"/api/v1/messages/{mid}/clear").json()["ok"]


def test_invalid_type_rejected(client, cfg):
    _, tok = auth.create_token("api-" + os.urandom(3).hex())
    r = client.post("/api/v1/messages", headers={"Authorization": f"Bearer {tok}"},
                    json={"source": "x", "type": "banana", "title": "t"})
    assert r.status_code == 422


def test_web_pages_render(client):
    for path in ("/", "/messages", "/tokens", "/settings", "/logs", "/docs"):
        assert client.get(path).status_code == 200
    assert client.get("/display.png").headers["content-type"] == "image/png"


def test_pinned_survives_restart(cfg):
    store.clear_all()
    mid = store.create_message("a", "error", "persist", pinned=True, priority=9)
    # re-open the DB (simulates process restart)
    db.init(cfg.get("database", "path"))
    assert store.active_message()["id"] == mid
