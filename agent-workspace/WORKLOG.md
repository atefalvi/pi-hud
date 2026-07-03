# WORKLOG

## 2026-07-02

- Work completed: Built pi-hud v1 end to end in one pass.
  - Package skeleton, `config.py` (INI + built-in defaults), `pyproject.toml`, `requirements.txt`.
  - `db.py` (WAL, single shared connection + write lock, idempotent schema), `message_store.py`
    (messages CRUD, active selection, queue grouping, logs, settings, snapshots, power events).
  - `auth.py` (ph_ tokens, sha256 hash-only storage, verify/revoke, first-token bootstrap).
  - `metrics.py` (psutil + thermal zone), `power.py` (`vcgencmd get_throttled` bit parser).
  - `drivers/st7735s.py` optimized from pi-rack-hud: configurable pins, SPI chunking,
    `display_if_changed()` frame hashing, `clear()`/`set_backlight()`, cached fonts, targeted
    GPIO cleanup, bounded SPI recovery, no numpy.
  - `renderer.py` (normal / alert / DNS / queue screens as 160x80 PIL images).
  - `display_loop.py` (background thread, headless fallback, power monitor, `build_frame()`).
  - `api.py` FastAPI: JSON API + Jinja2 web UI (dashboard, messages+detail, tokens, settings,
    logs, api docs) + `/display.png` live preview. `main.py` entrypoint.
  - Templates + `app.css` ported from the Observatory mockup; minimal `app.js`.
  - `install.sh` / `update.sh` / `uninstall.sh`, systemd unit template.
  - `tests/test_pi_hud.py` (15 tests).
- Files changed: see handoff summary.
- Tests run: `pytest` → 15 passed. Rendered all three HUD screens + web endpoints (all 200).
- Issues: Hardware (SPI/GPIO panel, vcgencmd) not verifiable off-Pi; covered by headless mode.
- Next: Run on the Pi 3B, confirm panel orientation/offsets, 24h idle CPU/memory check.
