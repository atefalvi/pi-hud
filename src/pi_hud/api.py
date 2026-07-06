"""FastAPI app: JSON API for apps + Jinja2 web UI for humans.

Auth model (v1, per SECURITY.md): message *creation* requires a bearer token
so only known apps can post. The web UI and management endpoints are
unauthenticated by design for a trusted local/LAN deployment — do not expose
pi-hud to the internet.
"""
import io
import json
import os
import signal
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import auth, db, display_loop
from . import message_store as store
from .config import Config
from .message_store import VALID_TYPES
from .models import MessageIn, TokenIn

_HERE = Path(__file__).parent
templates = Jinja2Templates(directory=str(_HERE / "templates"))


def friendly_time(value, default="—"):
    """UTC ISO string → 'July 4, 2026 at 9:30 PM EST' in the Pi's local zone.
    Non-parseable values pass through unchanged."""
    if not value:
        return default
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone()
    hour = dt.strftime("%I").lstrip("0") or "12"
    tz = dt.strftime("%Z")
    return (f"{dt.strftime('%B')} {dt.day}, {dt.year} at "
            f"{hour}:{dt.strftime('%M')} {dt.strftime('%p')} {tz}").rstrip()


templates.env.filters["friendly"] = friendly_time

# light in-memory rate limit for failed auth: ip -> (count, window_start)
_fails: dict[str, list] = {}
_FAIL_LIMIT, _FAIL_WINDOW = 8, 60


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    c = _fails.get(ip)
    if not c or now - c[1] > _FAIL_WINDOW:
        _fails[ip] = [0, now]
        c = _fails[ip]
    return c[0] >= _FAIL_LIMIT


def _record_fail(ip: str):
    _fails.setdefault(ip, [0, time.monotonic()])[0] += 1


def create_app(cfg: Config, loop: "display_loop.DisplayLoop") -> FastAPI:
    app = FastAPI(title="pi-hud", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        # surface server errors in the Logs page instead of a bare 500
        try:
            store.log("error", "web", "unhandled_exception",
                      f"{request.method} {request.url.path}: {type(exc).__name__}: {exc}")
        except Exception:
            pass
        if request.url.path.startswith("/api/") or request.method != "GET" and \
                "application/json" in request.headers.get("content-type", ""):
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
        return HTMLResponse(
            "<body style='background:#0A0C10;color:#EDEFF3;font-family:sans-serif;"
            "display:grid;place-items:center;height:100vh'><div style='max-width:48ch'>"
            f"<h2>Something broke</h2><p style='color:#A8B1BD'>{type(exc).__name__}: {exc}</p>"
            "<p><a href='/logs' style='color:#FF5C38'>See Logs</a> · "
            "<a href='/' style='color:#FF5C38'>Dashboard</a></p></div></body>",
            status_code=500)

    def require_token(request: Request, authorization: str = Header(default="")):
        ip = request.client.host if request.client else "?"
        if _rate_limited(ip):
            raise HTTPException(429, "too many failed auth attempts")
        token = authorization[7:] if authorization.startswith("Bearer ") else None
        if not auth.verify(token):
            _record_fail(ip)
            store.log("warning", "auth", "auth_failure", f"ip={ip}")
            raise HTTPException(401, "invalid or missing token")

    started = time.monotonic()

    # ---------------- JSON API ----------------
    @app.get("/health")
    def health():
        try:
            db.query_one("SELECT 1")
            dbs = "ok"
        except Exception:
            dbs = "error"
        from . import __version__
        return {"status": "ok", "display": loop.status, "database": dbs,
                "active_messages": store.active_count(),
                "version": __version__,
                "uptime_s": int(time.monotonic() - started)}

    @app.post("/api/v1/messages", dependencies=[Depends(require_token)])
    def create_message(m: MessageIn):
        mid = store.create_message(
            source=m.source, type=m.type, title=m.title, message=m.message,
            pinned=m.pinned, priority=m.priority, category=m.category,
            metadata=m.metadata)
        store.log("info", m.source, "message_created", f"id={mid} type={m.type}")
        return {"ok": True, "message_id": mid}

    @app.get("/api/v1/messages")
    def api_list(status: str = "all", limit: int = 50, offset: int = 0):
        return {"messages": [_row(r) for r in store.list_messages(status, limit, offset)]}

    @app.get("/api/v1/messages/{mid}")
    def api_detail(mid: int):
        r = store.get_message(mid)
        if not r:
            raise HTTPException(404, "not found")
        return _row(r)

    @app.post("/api/v1/messages/{mid}/clear")
    def api_clear(mid: int):
        return {"ok": store.clear_message(mid)}

    @app.post("/api/v1/messages/{mid}/protect")
    def api_protect(mid: int):
        return {"ok": store.set_message_protected(mid, True)}

    @app.post("/api/v1/messages/{mid}/unprotect")
    def api_unprotect(mid: int):
        return {"ok": store.set_message_protected(mid, False)}

    @app.post("/api/v1/messages/current/clear")
    def api_clear_current():
        return {"ok": store.clear_current() is not None}

    @app.post("/api/v1/messages/clear-all")
    def api_clear_all():
        return {"ok": True, "cleared": store.clear_all()}

    @app.post("/api/v1/tokens")
    def api_token_create(t: TokenIn):
        tid, plaintext = auth.create_token(t.name)
        store.log("info", "admin", "token_created", t.name)
        return {"ok": True, "id": tid, "token": plaintext}

    @app.post("/api/v1/tokens/{tid}/revoke")
    def api_token_revoke(tid: int):
        return {"ok": auth.revoke(tid)}

    @app.get("/preview.png")
    def preview_png(type: str = "success", title: str = "Title", message: str = "",
                    pinned: bool = True, source: str = "my-app", host: str = "",
                    record_type: str = "", previous_value: str = "",
                    updated_value: str = ""):
        """Render a demo alert frame from query params — used by the API-docs
        builder so users see exactly what the panel will show."""
        from . import renderer
        if type not in VALID_TYPES:
            type = "info"
        m = {"type": type, "title": title[:48] or "Title",
             "message": message[:500] or None, "pinned": pinned,
             "source": source[:64],
             "category": "dns" if previous_value and updated_value else None,
             "metadata": {"host": host, "record_type": record_type,
                          "previous_value": previous_value,
                          "updated_value": updated_value}}
        img = renderer.render_message(m).resize((320, 160))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return Response(buf.getvalue(), media_type="image/png",
                        headers={"Cache-Control": "no-store"})

    @app.get("/display.png")
    def display_png():
        img = display_loop.build_frame(cfg).resize((320, 160))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return Response(buf.getvalue(), media_type="image/png",
                        headers={"Cache-Control": "no-store"})

    # ---------------- Web UI ----------------
    from . import __version__, metrics
    device = {  # sidebar identity — which Pi am I looking at?
        "hostname": metrics.hostname(),
        "ip": metrics.lan_ip(),
        "port": cfg.getint("api", "port"),
        "version": __version__,
    }

    def page(request, name, **ctx):
        lan = cfg.getbool("api", "lan_mode") or cfg.get("api", "host") == "0.0.0.0"
        ctx.update(lan_mode=lan, device=device)
        return templates.TemplateResponse(request, name, ctx)

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request):
        am = store.display_message()
        return page(request, "dashboard.html", active=_row(am) if am else None,
                    active_count=store.display_count(), nav="dashboard")

    @app.get("/messages", response_class=HTMLResponse)
    def messages(request: Request, id: int | None = None, status: str = "all"):
        rows = [_row(r) for r in store.list_messages(status, 100)]
        selected = _row(store.get_message(id)) if id else (rows[0] if rows else None)
        return page(request, "messages.html", messages=rows, selected=selected,
                    status=status, nav="messages")

    @app.get("/messages/{mid}", response_class=HTMLResponse)
    def message_detail(request: Request, mid: int):
        return RedirectResponse(f"/messages?id={mid}")

    @app.get("/tokens", response_class=HTMLResponse)
    def tokens(request: Request):
        return page(request, "tokens.html", tokens=[dict(t) for t in auth.list_tokens()],
                    new_token=None, nav="tokens")

    @app.post("/tokens", response_class=HTMLResponse)
    async def tokens_create(request: Request):
        form = await request.form()
        name = (form.get("name") or "").strip()[:64]
        new = None
        if name:
            try:
                _, new = auth.create_token(name)
                store.log("info", "admin", "token_created", name)
            except Exception as e:
                new = None
                store.log("error", "admin", "token_create_failed", str(e))
        return page(request, "tokens.html", tokens=[dict(t) for t in auth.list_tokens()],
                    new_token=new, new_name=name, nav="tokens")

    @app.post("/tokens/{tid}/revoke")
    async def tokens_revoke(tid: int):
        auth.revoke(tid)
        return RedirectResponse("/tokens", status_code=303)

    @app.post("/tokens/{tid}/regenerate", response_class=HTMLResponse)
    async def tokens_regenerate(request: Request, tid: int):
        res = auth.regenerate(tid)
        name, new = res if res else (None, None)
        if new:
            store.log("info", "admin", "token_regenerated", name)
        return page(request, "tokens.html", tokens=[dict(t) for t in auth.list_tokens()],
                    new_token=new, new_name=name, nav="tokens")

    @app.get("/settings", response_class=HTMLResponse)
    def settings(request: Request):
        return page(request, "settings.html", cfg=cfg, overrides=store.all_settings(),
                    maintenance=store.maintenance_status(),
                    database=store.database_status(), nav="settings")

    @app.post("/settings")
    async def settings_save(request: Request):
        form = await request.form()
        for key in ("temp_warning_c", "temp_danger_c", "cpu_warning_percent",
                    "cpu_danger_percent", "ram_warning_percent", "ram_danger_percent",
                    "power_event_pinning", "database_target_mb"):
            if key in form and str(form[key]).strip():
                value = str(form[key]).strip()
                store.set_setting(key, value)
                if key == "power_event_pinning":
                    store.set_active_category_pinned("power", value == "true")
        store.log("info", "admin", "settings_updated", "")
        return RedirectResponse("/settings", status_code=303)

    @app.get("/settings/database/export")
    def settings_database_export():
        db.checkpoint()
        return FileResponse(
            path=str(db.path()),
            media_type="application/vnd.sqlite3",
            filename=f"pi-hud-{datetime.now(timezone.utc).date()}.db")

    @app.post("/settings/database/cleanup-logs")
    async def settings_cleanup_logs():
        store.cleanup_logs_keep_days(30)
        return RedirectResponse("/settings", status_code=303)

    @app.post("/settings/database/cleanup-messages")
    async def settings_cleanup_messages():
        store.cleanup_messages_keep_days(30)
        return RedirectResponse("/settings", status_code=303)

    # keys editable from the web UI, with light validation
    _CFG_INT = {("api", "port"), ("display", "rotation"), ("display", "x_offset"),
                ("display", "y_offset"), ("display", "dc_pin"), ("display", "rst_pin"),
                ("display", "bl_pin"), ("display", "spi_speed_hz"),
                ("display", "normal_refresh_seconds"), ("display", "power_refresh_seconds")}
    _CFG_BOOL = {("api", "lan_mode"), ("display", "enabled"),
                 ("display", "bgr"), ("display", "invert")}

    @app.post("/web/test-message")
    def web_test_message(m: MessageIn):
        """Send a message from the web UI (builder 'send to display'). Same
        trust model as the other web actions: local/LAN operator, no token."""
        mid = store.create_message(
            source=m.source, type=m.type, title=m.title, message=m.message,
            pinned=m.pinned, priority=m.priority, category=m.category,
            metadata=m.metadata)
        store.log("info", "web-ui", "test_message_created", f"id={mid}")
        return {"ok": True, "message_id": mid}

    @app.post("/settings/display-test")
    async def settings_display_test():
        loop.show_color_test()
        store.log("info", "admin", "display_color_test", "")
        return RedirectResponse("/settings", status_code=303)

    @app.post("/settings/config", response_class=HTMLResponse)
    async def settings_config(request: Request):
        form = await request.form()
        for section, key in _CFG_INT | _CFG_BOOL:
            v = str(form.get(key, "")).strip()
            if (section, key) in _CFG_INT and v.lstrip("-").isdigit():
                cfg._p.set(section, key, v)
            elif (section, key) in _CFG_BOOL and v in ("true", "false"):
                cfg._p.set(section, key, v)
        path = cfg.path or "/etc/pi-hud/config.ini"
        with open(path, "w") as f:
            cfg._p.write(f)
        store.log("info", "admin", "config_updated", path)
        # Let the response flush, then exit; systemd (Restart=always) brings us
        # back with the new config. Skipped under pytest so tests survive.
        if "PYTEST_CURRENT_TEST" not in os.environ:
            threading.Timer(
                1.0, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()
        return HTMLResponse(
            "<meta http-equiv='refresh' content='6;url=/settings'>"
            "<body style='background:#0A0C10;color:#EDEFF3;font-family:sans-serif;"
            "display:grid;place-items:center;height:100vh'>"
            f"<p>Config saved to {path}.<br>Service is restarting — "
            "this page reloads in a few seconds.</p></body>")

    @app.get("/logs", response_class=HTMLResponse)
    def logs(request: Request):
        return page(request, "logs.html", logs=[dict(r) for r in store.list_logs(150)],
                    power=[dict(r) for r in store.list_power_events(30)], nav="logs")

    @app.get("/docs", response_class=HTMLResponse)
    def apidocs(request: Request):
        host = cfg.get("api", "host")
        port = cfg.getint("api", "port")
        return page(request, "apidocs.html", host=host, port=port, nav="docs")

    return app


def _row(r) -> dict:
    """sqlite Row -> plain dict with parsed metadata."""
    d = dict(r)
    d["metadata"] = json.loads(d["metadata_json"]) if d.get("metadata_json") else {}
    return d
