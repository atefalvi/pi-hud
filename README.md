# pi-hud

**A display and notification hub for your home-lab rack, running on a Raspberry Pi.**

[![Release](https://img.shields.io/github/v/release/atefalvi/pi-hud)](https://github.com/atefalvi/pi-hud/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-c51a4a)

`pi-hud` owns an ST7735S 160×80 SPI display and turns it into a glanceable status
panel for the whole rack. Idle, it shows system vitals — hostname, temperature, CPU,
RAM, service badges. When any of your apps POSTs a message to its API, the panel
switches to a color-coded alert that stays pinned until you clear it from the web UI.
Every message is persisted in SQLite with full detail: source, payload, timeline.

Built to run 24/7 on a Pi 3B next to your other services: native systemd unit,
single Uvicorn worker, FastAPI + Jinja2 + vanilla JS. No Node, no Docker, no
build step.

## Features

- **Physical HUD** — system status screen, six alert severities, change screens
  (`A 203.0.113.42 → 198.51.100.27`), and a grouped pending queue when multiple
  alerts are active
- **Pinned alerts** — critical messages hold the screen until cleared; pins survive
  reboots
- **Web UI** — dashboard with a live picture of the physical panel, message browser
  with full detail and timeline, logs, and settings — including display pins, color
  calibration, and network mode, all editable in the browser
- **HTTP API** — any app or device can send messages with a bearer token; an
  interactive builder generates the `curl` command and previews the exact panel output
- **Token management** — per-app tokens, hash-only storage, one-click regenerate
- **Power monitoring** — watches `vcgencmd get_throttled`, logs undervoltage and
  throttling, raises panel alerts
- **Efficient by design** — differential display updates, no numpy, minimal
  dependencies, WAL SQLite

## Hardware

Any Raspberry Pi with SPI (tested on a Pi 3B) plus an ST7735S 0.96" 160×80 TFT.

| Panel pin | Pi signal      | BCM    | Physical pin |
|-----------|----------------|--------|--------------|
| VCC       | 3.3V           | —      | 1 or 17      |
| GND       | Ground         | —      | 6/9/14/20    |
| SCL/SCK   | SPI0 SCLK      | GPIO11 | 23           |
| SDA/MOSI  | SPI0 MOSI      | GPIO10 | 19           |
| CS        | SPI0 CE0       | GPIO8  | 24           |
| DC        | Data/Command   | GPIO25 | 22           |
| RST/RES   | Reset          | GPIO27 | 13           |
| BLK/BL    | Backlight      | GPIO24 | 18           |

Pins are configurable in `config.ini` or on the Settings page. Enable SPI first:
`sudo raspi-config` → Interface Options → SPI → reboot.

## Installation

```bash
git clone https://github.com/atefalvi/pi-hud.git
cd pi-hud
sudo ./install.sh
```

The installer creates a venv under `/opt/pi-hud`, writes `/etc/pi-hud/config.ini`,
initializes `/var/lib/pi-hud/pi-hud.db`, enables the `pi-hud` systemd service, and
prints the local URL plus your first API token (shown **once** — copy it).

Updating and removing:

```bash
sudo ./update.sh              # git pull, reinstall, migrate, restart, health check
sudo ./uninstall.sh           # remove service + app (keeps the database)
sudo ./uninstall.sh --purge   # also delete the database
```

## Usage

### Web UI

`http://127.0.0.1:8765` locally, or `http://<PI_IP>:8765` with LAN mode on.
Each Pi identifies itself in the sidebar (hostname, IP, version), so multiple
dashboards stay distinguishable.

### Sending messages

Create a token on the **Tokens** page, then:

```bash
curl -X POST http://127.0.0.1:8765/api/v1/messages \
  -H "Authorization: Bearer ph_xxx" -H "Content-Type: application/json" \
  -d '{
    "source": "pi-dns-sync",
    "type": "success",
    "title": "DNS Updated",
    "pinned": true,
    "category": "dns",
    "metadata": {
      "host": "home.example.com",
      "record_type": "A",
      "previous_value": "203.0.113.42",
      "updated_value": "198.51.100.27"
    }
  }'
```

The **API** page documents every field and its effect on the panel, and its builder
composes commands interactively with a live preview — including a "send to display"
test button. A same-Pi Docker example for `pi-dns-sync` is in
[`examples/`](examples/docker-compose.pi-dns-sync.yml).

### Configuration

Live thresholds (temperature/CPU/RAM warnings) apply instantly from the Settings
page. Infrastructure settings (port, display pins, SPI speed, color order) are in
`/etc/pi-hud/config.ini` — also editable from Settings; saving restarts the service
automatically.

By default the API binds `127.0.0.1` only. For other devices on your network set
`lan_mode = true` (Settings or config file). **Never expose pi-hud to the public
internet.**

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Panel static or blank | Check the wiring table above vs. Settings → pins; run the display triage tool below |
| Red/blue swapped | Settings → *Run color check*, then flip **BGR color order** |
| Colors look negative | Flip **Invert colors** in Settings |
| Web UI unreachable from LAN | Enable **LAN mode** in Settings |
| Anything else | The **Logs** page records server errors; `journalctl -u pi-hud -n 50` has the rest |

```bash
# drives the panel directly, step by step (stop the service first)
sudo systemctl stop pi-hud
sudo PI_HUD_CONFIG=/etc/pi-hud/config.ini \
  /opt/pi-hud/.venv/bin/python -m pi_hud.display_test   # --slow for 4 MHz
sudo systemctl start pi-hud
```

## Development

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e . && pip install pytest httpx
PYTHONPATH=src python -m pytest tests/ -q
```

The driver imports `spidev`/`RPi.GPIO` lazily, so everything except the physical
panel runs on a laptop (display reports `disabled`).

Design follows the DataDreamer Observatory direction — dark-first, hairline borders,
restrained ember accent. Specs, decision log, and test reports live in
[`agent-workspace/`](agent-workspace/).

## License

[MIT](LICENSE) © DataDreamer
