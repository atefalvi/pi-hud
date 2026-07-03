# Test Plan

## Unit tests

- Config parsing.
- Message validation.
- Token creation/hashing.
- Token revocation.
- Active message selection.
- Queue grouping.
- SQLite migrations.
- Power event parsing.
- API auth.
- Renderer text clamping.

## Integration tests

- POST message creates SQLite row.
- Active message appears on dashboard.
- Clear current changes message status.
- Pinned message survives process restart.
- Invalid token rejected.
- Revoked token rejected.
- Message detail page shows metadata.

## Hardware tests

On Raspberry Pi:

- Display initializes.
- Normal status screen renders.
- DNS update screen renders.
- Pending queue screen renders without overlap.
- Alert stays until cleared.
- Clear button in web UI returns display to normal.
- `vcgencmd get_throttled` parser logs power events.

## Performance tests

On Raspberry Pi 3B:

- CPU low at idle.
- Memory stable over 24 hours.
- No constant redraw for pinned screen.
- Web UI loads quickly on LAN.
