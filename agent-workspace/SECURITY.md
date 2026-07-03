# Security

## Defaults

- Default API host: `127.0.0.1`.
- LAN mode must be explicit.
- No public internet exposure.
- All write endpoints require bearer token.
- Tokens are shown once at creation.
- Store only hashed tokens.
- Log auth failures.
- Rate-limit token failures lightly.

## Token format

Generated tokens should look like:

```text
ph_<random>
```

Example:

```text
ph_7b9ce1c98a...
```

Store:

- prefix
- hash
- created timestamp
- last used timestamp
- revoked timestamp

Never store plaintext token after creation.

## Web UI

For v1, local network web UI does not require user login if LAN protected, but destructive actions should require a configured admin token or local-only access. Agent may implement a simple admin token prompt if practical.

## CORS

Disable open CORS.

No wildcard browser-origin write access.

## LAN mode warning

If `api_host = 0.0.0.0`, show a warning in Settings:

```text
LAN mode is enabled. Do not port-forward pi-hud.
```
