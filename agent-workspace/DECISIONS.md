# DECISIONS

Record any implementation decision that changes, clarifies, or deviates from the PRD.

## Decision template

```text
Date:
Decision:
Reason:
Files affected:
Tradeoffs:
```

## Current fixed decisions

- Project name: `pi-hud`.
- Display service is native systemd, not Docker.
- Frontend is FastAPI + Jinja2 + static CSS.
- No React/Vue/Node/Tailwind in v1.
- SQLite is used for messages, logs, tokens, system snapshots, and power events.
- Pending queue screen shows grouped rows and counts only, with no bottom badge pile.

## Implementation decisions (2026-07-04, second pass)

```
Decision: Display pins corrected to the old pi-rack-hud driver defaults — DC=GPIO25,
          RST=GPIO27, BL=GPIO24 (BCM).
Reason:   User confirmed the old driver worked with their wiring; the handoff docs'
          pins (23/24/18) were wrong — DRIVER_OPTIMIZATION.md's suspected "docs/code pin
          mismatch" is confirmed, code was right. Blank/static panel on first install
          was caused by driving the wrong pins.
Files:    config.py, config.example.ini, drivers/st7735s.py, README.md (wiring table)
Tradeoffs: Existing /etc/pi-hud/config.ini keeps old values — fix via Settings page or sed.
```

```
Decision: Tokens stay hash-only; "copy existing token" is served by a Regenerate action
          (revoke + reissue under the same name, shown once) plus a copy button on the
          reveal that works over plain http.
Reason:   Recoverable tokens would require plaintext storage, which SECURITY.md forbids.
Files:    auth.py (regenerate), api.py, tokens.html, app.js (copyText fallback)
```

```
Decision: Config file editable from the Settings page; saving writes the INI and the
          process exits ~1s later so systemd (Restart=always) reboots it with new values.
Reason:   The service user owns /etc/pi-hud but cannot run systemctl; exiting is the
          zero-privilege restart. In dev (no systemd) the process just exits.
Files:    api.py (/settings/config), settings.html
Tradeoffs: Only whitelisted int/bool keys accepted; bad values are ignored not errored.
```

## Implementation decisions (2026-07-04)

```
Decision: `lan_mode = true` binds 0.0.0.0 directly; the `host` key is only used when
          lan_mode is false. One switch instead of two coupled keys.
Reason:   First install showed lan_mode was cosmetic — users flip the documented flag and
          expect LAN access. Default stays 127.0.0.1 (SECURITY.md: LAN must be explicit).
Files:    main.py, api.py (warning banner), README.md, install.sh
Tradeoffs: `host` is ignored when lan_mode=true; documented in README.
```

```
Decision: SPI pixel data goes through `writebytes2()` (buffer protocol) instead of
          chunked `xfer2()`; xfer2 kept only for small command-argument lists.
Reason:   xfer2 with large `bytes` payloads mishandles data on current py-spidev —
          observed as full-screen static on first hardware install.
Files:    drivers/st7735s.py
Tradeoffs: Requires py-spidev >= 3.4 (2019); fine.
```

## Implementation decisions (2026-07-02)

```
Decision: Two-tier config — INI file for infrastructure (host/port/pins/SPI),
          SQLite `settings` table for live-tunable values (thresholds, power pinning).
Reason:   Network/pin changes need a restart anyway; thresholds should apply live from
          the Settings page without editing files. Settings table only holds overrides;
          config.ini provides the fallback default, so no seeding/duplication step.
Files:    config.py, message_store.get_setting/set_setting, display_loop._threshold, api.py
Tradeoffs: A value can live in two places, but the override-with-fallback rule is unambiguous.
```

```
Decision: Auth only on POST /api/v1/messages (bearer token required). Web UI and
          management/clear/token endpoints are unauthenticated.
Reason:   SECURITY.md: trusted local/LAN, no user accounts in v1. Apps must authenticate;
          the local operator on the LAN is trusted. Light in-memory rate limit on auth
          failures; auth failures logged.
Files:    api.py, auth.py, SECURITY.md
Tradeoffs: Anyone on the LAN can clear alerts / manage tokens. Acceptable for v1 (do not
           expose to internet). Revisit with an admin token if LAN is untrusted.
```

```
Decision: `/display.png` renders the live HUD frame server-side and the dashboard shows it
          via <img>, instead of re-implementing the HUD in HTML.
Reason:   One renderer, one source of truth; the web preview is pixel-accurate to the panel.
Files:    api.py, display_loop.build_frame, renderer.py
Tradeoffs: A small PNG encode every few seconds; negligible on a 160x80 image.
```

```
Decision: Service runs as the installing user (SUDO_USER, usually `pi`) added to spi,gpio
          groups, rather than a dedicated locked-down system user.
Reason:   SPI/GPIO access needs group membership; the pi user already has it. Simpler install,
          fewer moving parts for a home v1.
Files:    install.sh, systemd/pi-hud.service.template
Tradeoffs: Less privilege separation than a dedicated user. Documented in INSTALL notes.
```

```
Decision: Power-dip conditions become a normal pinned message (source=system, category=power)
          rather than a separate display code path.
Reason:   Reuses the message/screen/clear pipeline; power caution screen falls out for free.
Files:    display_loop._check_power / _ensure_power_message.
Tradeoffs: None significant; one active power message at a time (deduped by category).
```

