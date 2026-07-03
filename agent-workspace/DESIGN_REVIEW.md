# DESIGN_REVIEW

Reviewed against `agent-workspace/assets/pi-hud-final-mockups.html` and DESIGN_SYSTEM.md.

## Checklist

- [x] Matches DataDreamer Observatory dark-first direction. — `--bg-0..3` dark surfaces, ember accent, same tokens as the mockup.
- [x] Uses ember accent sparingly. — Accent only for active nav, primary button, live dot, timeline nodes, caution rail.
- [x] Uses hairline borders instead of heavy shadows. — 1px `--border-1/2` throughout; no drop shadows in the web UI.
- [x] Does not repeat `OK` labels. — Status is conveyed by coloured badges/rails/dots; no "OK" text spam.
- [x] Uses coloured badges/dots/rails for state. — `.sev`, `.chip`, badge pile, queue rails, alert rail.
- [x] Pending queue screen has no bottom badge pile. — `render_queue()` draws grouped rails + counts only.
- [x] DNS update screen clearly shows old IP → new IP. — `A <old> → <new>` on the panel; old/new/record stats on the dashboard.
- [x] Message detail page shows full message information. — source, created/ack/cleared, host, record type, previous/updated value, body, raw JSON, timeline, clear.
- [x] No emoji icons. — Nav uses geometric glyphs (▣ ◇ ◈ ◎ ☰ {}); alert glyphs are text (✓/×/!). No emoji.
- [x] No heavy frontend framework. — FastAPI + Jinja2 + one static CSS + ~20 lines of vanilla JS. No build step.
- [x] Mobile web UI is usable. — Sidebar collapses, grids drop to single column at ≤900px.
- [x] Focus states are visible. — `:focus-visible` outlines on buttons and inputs.

## Notes / deliberate deviations

- Alert type glyph uses `✓ / × / !` text instead of the mockup's icon chips — avoids bundling an
  icon font and keeps the panel legible at 160×80 with the mono font. Colour + rail carry the state.
- Serif display font is Georgia (system serif) rather than Fraunces to avoid a web-font fetch/build;
  DESIGN_SYSTEM allows "Fraunces-like serif … if available".
- Normal-screen service badges are DNS / API / PWR. API/DNS are green while the service is up; PWR
  reflects the latest `vcgencmd` reading. Per-service health probing was intentionally left out of v1.
- Web dashboard's "Current display" is the real rendered panel image (`/display.png`), so what you see
  in the browser is exactly what is on the physical screen.

## Verdict

Aligned with the Observatory direction. No neon/gradient-mesh/glass anti-patterns present.
