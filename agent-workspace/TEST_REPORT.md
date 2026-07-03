# TEST_REPORT

## Environment

```text
Device:      Development machine (macOS, darwin 24.6.0) — headless display mode
OS:          macOS (target device: Raspberry Pi OS on Pi 3B)
Python:      3.14 (dev); target requires >=3.11
Display:     ST7735S 160x80 — not attached in dev; renderer verified via PIL images
SPI enabled: N/A in dev
```

## Tests run

- [x] Unit tests — config, store, auth, power parser, renderer clamping
- [x] API tests — health, auth required/rejected, create+detail+clear, invalid type 422
- [x] Web UI smoke test — /, /messages, /tokens, /settings, /logs, /docs all 200; /display.png image/png
- [x] SQLite migration test — schema is idempotent (`CREATE TABLE IF NOT EXISTS`); re-init verified
- [x] Token auth test — create/verify/revoke; hash-only storage asserted
- [ ] Display hardware test — REQUIRES Pi (SPI panel). Renderer output verified as images.
- [ ] Long-running idle test — REQUIRES Pi (24h CPU/memory).
- [x] Power monitor parser test — `0x50005` → undervoltage+throttle now+occurred; `0x0` clean

## Results

`pytest` → **15 passed** in 0.19s.

Verified behaviours:
- Active message selection orders by `priority DESC, created_at ASC`.
- Queue grouping collapses types into Error / Power / Info, most-severe first.
- Pinned message survives a simulated process restart (DB re-init).
- Invalid `type` rejected with 422; missing/invalid token rejected with 401.
- Rendered screens (normal, DNS updated, pending queue, error, boot) are all 160x80.

### Rendered screen samples (dev)
- Normal: hostname, temp + live dot, CPU/RAM bars, DNS/API/PWR badge pile. ✔ matches mockup 01.
- DNS updated: green rail, `✓ SUCCESS` + PIN, `DNS Updated`, `A old → new`, host footer. ✔ matches mockup 02.
- Pending queue: `N pending` + live dot, grouped rails + counts, no badge pile. ✔ matches mockup 03.

## Pending on-hardware checklist (run on the Pi 3B)

1. `dtparam=spi=on` enabled, reboot, panel wired to configured pins (DC=23, RST=24, BL=18).
2. `sudo systemctl status pi-hud` active; boot screen then normal status appears.
3. POST a DNS message → pinned DNS screen renders; clear from web UI → returns to normal.
4. Force multiple active messages → pending queue screen (no overlap, no bottom badges).
5. `vcgencmd get_throttled` under load → power event logged, Power Dip message pinned.
6. `top`/`systemd-cgtop` idle CPU low; memory stable over 24h; confirm no constant redraw
   (pinned screen writes once — `display_if_changed` frame hash).
