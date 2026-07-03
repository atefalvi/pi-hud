# Agent Instructions

## Mission

Build `pi-hud` in one focused pass as a lightweight Raspberry Pi 3B notification display and web-managed message hub.

## Hard constraints

- Keep it fast.
- Keep it simple.
- Keep it secure.
- Optimize for Raspberry Pi 3B.
- Avoid heavy dependencies.
- Do not add React, Vue, Node, Tailwind, or a frontend build step.
- Use FastAPI + Jinja2 + static CSS + minimal vanilla JS.
- Run Uvicorn as a single worker.
- Use SQLite for persistence.
- Use systemd for runtime.
- Do not expose the service to the internet.
- Do not let sender apps control the display directly.

## Required agent progress files

Create and maintain these files under `agent-workspace/`:

```text
WORKLOG.md
TASKS.md
DECISIONS.md
TEST_REPORT.md
DESIGN_REVIEW.md
```

Update them continuously.

## Required implementation order

1. Create package structure.
2. Add config loader.
3. Add SQLite schema and database helpers.
4. Add message store.
5. Add token auth.
6. Add FastAPI API endpoints.
7. Add Jinja2 frontend.
8. Add metrics and power monitor.
9. Add display renderer.
10. Integrate ST7735S driver.
11. Add systemd service.
12. Add installer.
13. Add tests.
14. Run design review.
15. Run final test report.

## Display ownership rule

Only `pi-hud` owns the physical display.

Other apps send messages through the API:

```text
POST /api/v1/messages
```

## Documentation rule

Any deviation from this package must be recorded in:

```text
agent-workspace/DECISIONS.md
```
