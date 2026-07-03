# HUD Screen Specification

## Hardware

- Display: ST7735S 160×80 landscape.
- Mockups show 2× scale.
- Physical render target remains 160×80 pixels.

## General rendering rules

- Use short text.
- Clamp long titles.
- Limit message body to two short lines.
- Alert screen should be mostly static.
- Do not redraw static pinned alerts every second.
- Normal screen refresh: 2 seconds.
- Power state refresh: 10 seconds.
- Metrics refresh: 2–5 seconds depending on metric.
- Use the DataDreamer Observatory color tokens.

## Screen 01 — Normal status

Purpose: shown when no active pinned alert exists.

Layout:

```text
┌────────────────────────┐
│ rack-pi          52°  ● │
│ CPU █████░░ 34%        │
│ RAM ██████░ 61%        │
│ DNS     API     PWR    │
└────────────────────────┘
```

Rules:

- `52°` is colored by temperature threshold.
- CPU/RAM values are colored by thresholds.
- Bottom badges are compact badge piles.
- The ember dot indicates live service/display loop.

Badge examples:

```text
DNS
API
PWR
NET
DB
```

## Screen 02 — DNS updated

Purpose: shown when `pi-dns-sync` updates Cloudflare successfully.

Layout:

```text
┌────────────────────────┐
││ ✓ Success        PIN  │
││ DNS Updated           │
││ A old-ip → new-ip     │
││ home.example.com clear│
└────────────────────────┘
```

Example:

```text
DNS Updated
A 203.0.113.42 → 198.51.100.27
home.example.com
```

Rules:

- Show old IP → new IP on physical HUD.
- Show host in footer.
- Keep full details in web UI.
- Use success green rail.
- PIN means pinned until cleared.

## Screen 03 — Pending queue

Purpose: shown when there are multiple pending messages.

This screen must not show bottom badges because space is limited.

Layout:

```text
┌────────────────────────┐
│ 4 pending             ● │
│ █ Error alerts       1 │
│ █ Power alerts       2 │
│ █ Info alerts        1 │
└────────────────────────┘
```

Rules:

- Group by message type.
- Show counts only.
- No bottom badge pile.
- No individual message titles.
- Use severity rails for each group.
- Maximum three groups shown:
  1. Critical/Error
  2. Power/Warning/Caution
  3. Info/Success/Note
- If more groups exist, combine lower priority groups under `Other`.

## Screen 04 — Error

Purpose: shown when app reports failure.

Layout:

```text
Error
DNS Failed
Cloudflare API rejected update request.
```

Rules:

- Red rail.
- Short message.
- Full details in Messages page.

## Screen 05 — Power caution

Purpose: undervoltage or throttling event.

Example:

```text
Power Dip
Undervoltage detected.
```

Rules:

- Use ember for caution.
- Use danger red for active undervoltage.
- Persist until cleared if power issue is severe.
