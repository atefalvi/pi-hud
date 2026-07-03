# Frontend Specification

## Stack

- FastAPI
- Jinja2
- Static CSS
- Minimal vanilla JS
- No SPA framework
- No build step

## Pages

```text
/                  Dashboard
/messages          Message center
/messages/{id}     Message detail, optional route or same-page panel
/tokens            App token management
/settings          Device and API settings
/logs              Logs and power events
/docs              API usage examples
/health            JSON health endpoint
```

## Dashboard

Purpose:

- Show current physical display preview.
- Show active alert summary.
- Provide clear current / clear all controls.
- Show status pile and metrics.

Required sections:

1. Current Display
2. Active Alert Summary
3. Status Pile
4. Metrics
5. Power warning callout if applicable

Dashboard DNS example:

```text
Current display:
DNS Updated
A 203.0.113.42 → 198.51.100.27

Summary:
Old IP: 203.0.113.42
New IP: 198.51.100.27
Record: A
Host: home.example.com
```

## Messages page

Purpose:

The user must be able to read every message and all details.

Layout:

```text
┌───────────────┬─────────────────────────┐
│ All messages  │ Selected message detail │
│ list          │ full details            │
└───────────────┴─────────────────────────┘
```

Message list row fields:

- severity
- title
- source
- host/summary
- pinned status
- created time
- action button

Selected detail fields:

- title
- severity
- source
- created timestamp
- acknowledged timestamp
- cleared timestamp
- host
- record type
- previous value
- updated value
- message body
- raw payload
- timeline

DNS detail example:

```text
Title: DNS Updated
Source: pi-dns-sync
Host: home.example.com
Record type: A
Previous value: 203.0.113.42
Updated value: 198.51.100.27
Message:
WAN IP changed. Cloudflare DNS record for home.example.com was updated successfully from 203.0.113.42 to 198.51.100.27.
```

Timeline example:

```text
14:16:59 Detection
14:17:01 Cloudflare request
14:17:03 Cloudflare response
14:17:04 HUD dispatch
```

## Tokens page

Purpose:

- Create app token.
- Revoke token.
- Show last used timestamp.
- Show token prefix only after creation.

Rules:

- Token visible only once at creation.
- Store hashed token only.
- Use one token per app.

## Settings page

Fields:

- API host
- API port
- LAN mode enabled
- display rotation
- display x/y offset
- refresh intervals
- temperature warning threshold
- temperature danger threshold
- CPU/RAM warning threshold
- power event pinning behavior

## Logs page

Show:

- API requests
- message events
- auth failures
- display errors
- power events
- system service restarts

## API Docs page

Show curl examples for:

- same-Pi request
- LAN request
- DNS update message
- warning message
- clear message
