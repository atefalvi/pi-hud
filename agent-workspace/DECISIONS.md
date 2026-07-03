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

