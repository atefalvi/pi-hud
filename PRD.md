# PRD — pi-hud

## 1. Product summary

`pi-hud` is a lightweight Raspberry Pi display and notification hub for a home-lab mini rack.

It runs on a Raspberry Pi 3B with an ST7735S 160×80 SPI display. It shows system status by default and switches to persistent alert screens when apps send important messages. Alerts can be cleared from a local web UI without SSH.

The first companion app is `pi-dns-sync`, which will update Cloudflare DNS and send `DNS Updated` or `DNS Failed` messages to `pi-hud`.

## 2. Product principles

1. Fast on Raspberry Pi 3B.
2. Simple to install and recover.
3. Secure by default.
4. Native display service owns the SPI screen.
5. Other apps only send messages.
6. No heavy frontend stack.
7. Persistent alerts survive reboot.
8. Every message can be inspected later in the web UI.

## 3. Final architecture

```text
Raspberry Pi 3B
├─ pi-hud.service
│  ├─ display loop
│  ├─ FastAPI server
│  ├─ Jinja2 web UI
│  ├─ SQLite database
│  ├─ power/voltage monitor
│  └─ ST7735S display driver
│
└─ pi-dns-sync
   ├─ Docker or systemd app
   └─ sends messages to pi-hud API
```

## 4. Runtime modes

### 4.1 Local-only mode

Used when only apps on the same Pi send messages.

```ini
api_host = 127.0.0.1
api_port = 8765
```

### 4.2 LAN mode

Used when other home-lab devices send messages.

```ini
api_host = 0.0.0.0
api_port = 8765
```

Other devices call:

```text
http://<PI_IP_ADDRESS>:8765/api/v1/messages
```

Do not expose this service to the public internet.

## 5. Tech stack

- Python 3.11+
- FastAPI
- Uvicorn, single worker
- Jinja2 templates
- SQLite
- Pillow
- psutil
- RPi.GPIO or gpiozero
- spidev
- PyYAML or configparser
- systemd service
- No React
- No Vue
- No Node build step
- No Tailwind build step

## 6. Package layout

```text
pi-hud/
├─ README.md
├─ PRD.md
├─ install.sh
├─ update.sh
├─ uninstall.sh
├─ pyproject.toml
├─ requirements.txt
├─ config.example.ini
├─ systemd/
│  └─ pi-hud.service.template
├─ src/
│  └─ pi_hud/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ config.py
│     ├─ db.py
│     ├─ models.py
│     ├─ metrics.py
│     ├─ power.py
│     ├─ message_store.py
│     ├─ renderer.py
│     ├─ display_loop.py
│     ├─ api.py
│     ├─ auth.py
│     ├─ templates/
│     ├─ static/
│     └─ drivers/
│        └─ st7735s.py
├─ agent-workspace/
└─ tests/
```

## 7. Core user stories

### US-001 — See rack status

As the owner, I want the Pi display to show CPU, RAM, temperature, and system service status when no alerts are active.

### US-002 — See persistent DNS update

As the owner, I want the physical HUD to show when `pi-dns-sync` updates DNS and keep it visible until I clear it.

### US-003 — Clear message without SSH

As the owner, I want to clear the current message from a web UI on my phone or laptop.

### US-004 — Read complete message details

As the owner, I want to open the web UI and read the complete details behind any message, including raw JSON and timeline.

### US-005 — Send message from another device

As the owner, I want another home-lab device to send an authenticated message to `pi-hud`.

### US-006 — Manage tokens

As the owner, I want to create and revoke app tokens from the web UI.

### US-007 — Monitor power issues

As the owner, I want `pi-hud` to detect undervoltage/throttling events and log them because the Pi has previously shut down due to voltage issues.

## 8. Non-goals for v1

- No internet exposure.
- No user accounts.
- No OAuth.
- No Discord bot in v1.
- No animated SPA frontend.
- No graph-heavy dashboard.
- No Docker for `pi-hud` v1 because it controls SPI/GPIO hardware.

## 9. Acceptance criteria

- Installer sets up a Python venv.
- Installer creates `/opt/pi-hud`, `/etc/pi-hud`, and `/var/lib/pi-hud`.
- Service starts on boot.
- Normal HUD renders without active messages.
- DNS update message renders on the physical HUD.
- Pinned messages survive reboot.
- Web UI can clear current message.
- Web UI can show full message details.
- App token can be created and revoked.
- Requests without valid token are rejected.
- LAN mode is optional and explicit.
- SQLite WAL mode is enabled.
- Power events are recorded when `vcgencmd get_throttled` reports a warning state.
- CPU usage remains low on Raspberry Pi 3B.
