# TASKS

## Phase 0 — Setup

- [x] Create repository `pi-hud`.
- [x] Add package structure.
- [x] Copy DataDreamer logo asset into `src/pi_hud/static/brand/`.
- [x] Copy or adapt ST7735S driver from `pi-rack-hud`.

## Phase 1 — Core backend

- [x] Config loader.
- [x] SQLite schema.
- [x] Message store.
- [x] Token auth.
- [x] Power monitor.
- [x] Metrics collector.

## Phase 2 — API

- [x] Health endpoint.
- [x] Message create endpoint.
- [x] Message list endpoint.
- [x] Message detail endpoint.
- [x] Clear current endpoint.
- [x] Clear all endpoint.
- [x] Token create/revoke endpoints.

## Phase 3 — Web UI

- [x] Dashboard.
- [x] Messages page with detail panel.
- [x] Tokens page.
- [x] Settings page.
- [x] Logs page.
- [x] API docs page.

## Phase 4 — Physical HUD

- [x] Normal status screen.
- [x] DNS updated screen.
- [x] Pending queue grouped screen.
- [x] Error screen. (generic alert renderer covers all severities)
- [x] Power caution screen. (power dip becomes a pinned message → alert screen)
- [x] Boot screen.
- [~] Display fallback screen. (headless mode logs + serves web preview; no on-panel fallback art in v1)

## Phase 5 — Install and QA

- [x] install.sh
- [x] update.sh
- [x] uninstall.sh
- [x] systemd service.
- [x] Tests. (15 passing)
- [ ] Performance check on Pi 3B. (requires hardware — see TEST_REPORT)
- [x] Design review.
- [x] Final handoff.
