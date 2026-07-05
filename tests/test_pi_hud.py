"""pi-hud test suite. Covers config, store, auth, power parsing, renderer,
and the HTTP API. Uses a temp SQLite DB and a headless display."""
import os
import re
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


def test_token_regenerate(cfg):
    tid, old = auth.create_token("regen-" + os.urandom(3).hex())
    name, new = auth.regenerate(tid)
    assert new.startswith("ph_") and new != old
    assert not auth.verify(old)      # old token dead
    assert auth.verify(new)          # replacement works
    active = [t for t in auth.list_tokens() if t["name"] == name and t["is_active"]]
    assert len(active) == 1


def test_preview_png(client):
    r = client.get("/preview.png", params={
        "type": "success", "title": "DNS Updated",
        "previous_value": "1.1.1.1", "updated_value": "2.2.2.2",
        "record_type": "A", "host": "h.example.com"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    # unknown type falls back instead of erroring
    assert client.get("/preview.png", params={"type": "banana"}).status_code == 200


def test_generic_change_line_screen():
    # change-line screen no longer requires category == "dns"
    img = renderer.render_message({
        "type": "info", "title": "Version Bump", "message": None, "pinned": 1,
        "source": "updater", "category": "software",
        "metadata": {"previous_value": "1.2.0", "updated_value": "1.3.0"}})
    assert img.size == (160, 80)
    assert renderer.render_colorcheck().size == (160, 80)


def test_web_test_message(client, cfg):
    store.clear_all()
    r = client.post("/web/test-message", json={
        "source": "web-ui", "type": "note", "title": "Builder Test"})
    assert r.status_code == 200 and r.json()["ok"]
    assert store.active_count() == 1
    # still validates
    assert client.post("/web/test-message", json={
        "source": "x", "type": "nope", "title": "t"}).status_code == 422


def test_health_has_version(client):
    j = client.get("/health").json()
    assert "version" in j and "uptime_s" in j


def test_settings_form_post(client, cfg):
    # HTML form posts require python-multipart; this guards the dependency
    r = client.post("/settings", data={"temp_warning_c": "60",
                                       "power_event_pinning": "false"},
                    follow_redirects=False)
    assert r.status_code == 303
    assert store.get_setting("temp_warning_c") == "60"


def test_tokens_form_post(client, cfg):
    name = "form-" + os.urandom(3).hex()
    r = client.post("/tokens", data={"name": name})
    assert r.status_code == 200
    assert "ph_" in r.text  # one-time reveal rendered
    tid = [t["id"] for t in auth.list_tokens() if t["name"] == name][0]
    assert client.post(f"/tokens/{tid}/revoke",
                       follow_redirects=False).status_code == 303
    assert client.post(f"/tokens/{tid}/regenerate").status_code == 200


def test_config_form_post(client, cfg, tmp_path):
    # point the config at a temp file so the test doesn't rewrite the repo's ini
    orig = cfg.path
    cfg.path = str(tmp_path / "config.ini")
    try:
        r = client.post("/settings/config", data={"port": "8765", "lan_mode": "false",
                                                  "rotation": "270", "bgr": "true"})
        assert r.status_code == 200
        assert "restarting" in r.text
        assert (tmp_path / "config.ini").exists()
    finally:
        cfg.path = orig


def test_friendly_time():
    from pi_hud.api import friendly_time
    out = friendly_time("2026-07-05T01:30:00+00:00")
    # local-zone dependent, but shape is fixed: "July 4, 2026 at 9:30 PM EDT"
    assert re.match(r"^[A-Z][a-z]+ \d{1,2}, \d{4} at \d{1,2}:\d{2} [AP]M", out)
    assert friendly_time(None) == "—"
    assert friendly_time(None, "never") == "never"
    assert friendly_time("not-a-date") == "not-a-date"  # passes through


def test_pinned_survives_restart(cfg):
    store.clear_all()
    mid = store.create_message("a", "error", "persist", pinned=True, priority=9)
    # re-open the DB (simulates process restart)
    db.init(cfg.get("database", "path"))
    assert store.active_message()["id"] == mid
