# WORKLOG

## 2026-07-04 (third pass) — color fix, generic API, send-test

- Panel showed orange as blue → red/blue channel swap: panel wants BGR order.
  Added MADCTL BGR bit + `bgr` config knob (default true, matches user's panel) and
  `invert` knob. Both editable in Settings.
- Settings gains "Run color check on display": shows labeled RED/GRN/BLU/EMBR/WHT bars
  on the panel for ~20s (display loop holds a test frame), with instructions to flip
  bgr/invert based on what's seen.
- De-DNS'd the API: change-line screen now triggers on previous+updated metadata for any
  app (versions, IPs, config values); record_type is an optional label; builder defaults
  and field reference reworded generically; dashboard stats now Previous/Updated/Type.
- Builder gains "Send to display (test)" → POST /web/test-message (unauthenticated,
  same web-UI trust model, validated by MessageIn).
- /health now reports version + uptime_s.
- Tests: 20 passed. Verified builder send, color-test endpoint, health in browser.

## 2026-07-04 (later) — root cause found: wrong pins; UX round

- display_test showed no colors at all → user supplied the old *working* driver, whose
  defaults are DC=25/RST=27/BL=24 (BCM). Handoff docs said 23/24/18 — docs were wrong.
  Defaults corrected everywhere + README wiring table added.
- Tokens: copy button on the one-time reveal (http-safe fallback), Regenerate action
  (revoke + reissue same name, shown once). Hash-only storage unchanged.
- Settings: config.ini now editable from the web UI; save writes the file and exits so
  systemd restarts with new values.
- API page: full field reference (what each field does + where it renders), request
  builder generating the curl command, live panel preview via new /preview.png.
- Tests: 17 passed. Verified builder/settings/tokens pages in browser preview.

## 2026-07-04 — field fixes after first install on the Pi

- Symptom: panel backlit but full-screen random static; web UI unreachable from LAN.
- Root causes:
  1. Pixel frames were sent as `bytes` through `spi.xfer2()`, which mishandles large
     bytes payloads on current py-spidev — init commands (small int lists) worked, so the
     panel powered on showing uninitialized GRAM. Fixed: `writebytes2()` for buffer data.
  2. `_recover()` could recurse (recovery re-runs init, whose failed writes re-enter
     recovery). Fixed with a `_recovering` guard.
  3. `lan_mode = true` was cosmetic; the server only bound the configured host. Fixed:
     lan_mode now binds 0.0.0.0 (default remains 127.0.0.1 local-only).
- Added `pi_hud/display_test.py` hardware triage tool (color cycle + wiring hints,
  `--slow` for 4MHz). install.sh prints health JSON + LAN/triage hints; update.sh now
  git-pulls and health-checks. README: LAN config + Troubleshooting section.
- Tests: 15 passed.

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
