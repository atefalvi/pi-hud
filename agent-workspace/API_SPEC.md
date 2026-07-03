# API Specification

## Authentication

All write endpoints require:

```http
Authorization: Bearer <token>
```

Tokens are created in the web UI.

Store only token hashes in SQLite.

## Endpoints

### GET /health

Response:

```json
{
  "status": "ok",
  "display": "ok",
  "database": "ok",
  "active_messages": 1
}
```

### POST /api/v1/messages

Create a message.

Request:

```json
{
  "source": "pi-dns-sync",
  "type": "success",
  "title": "DNS Updated",
  "message": "Cloudflare record updated.",
  "pinned": true,
  "priority": 5,
  "category": "dns",
  "metadata": {
    "host": "home.example.com",
    "record_type": "A",
    "previous_value": "203.0.113.42",
    "updated_value": "198.51.100.27"
  }
}
```

Response:

```json
{
  "ok": true,
  "message_id": 123
}
```

Validation:

- `source`: required, max 64 chars.
- `type`: one of `success`, `info`, `note`, `warning`, `caution`, `error`, `critical`.
- `title`: required, max 48 chars.
- `message`: max 500 chars.
- `pinned`: default false.
- `priority`: 1–10.
- `metadata`: JSON object, max 4096 chars when serialized.

### GET /api/v1/messages

List messages.

Query params:

```text
status=active|cleared|all
limit=50
offset=0
```

### GET /api/v1/messages/{id}

Return full message detail.

### POST /api/v1/messages/{id}/clear

Clear a message.

### POST /api/v1/messages/current/clear

Clear current active message.

### POST /api/v1/messages/clear-all

Clear all active messages.

### POST /api/v1/tokens

Create token.

### POST /api/v1/tokens/{id}/revoke

Revoke token.

## pi-dns-sync same-Pi Docker integration

```yaml
services:
  pi-dns-sync:
    image: ghcr.io/atefalvi/pi-dns-sync:latest
    container_name: pi-dns-sync
    network_mode: host
    restart: unless-stopped
    environment:
      HUD_URL: "http://127.0.0.1:8765"
      HUD_TOKEN: "your-token"
```

## LAN device example

```bash
curl -X POST http://192.168.10.42:8765/api/v1/messages   -H "Authorization: Bearer ph_xxx"   -H "Content-Type: application/json"   -d '{
    "source": "nas-backup",
    "type": "success",
    "title": "Backup Done",
    "message": "TrueNAS sync finished",
    "pinned": false,
    "priority": 3
  }'
```
