# pi-hud

A lightweight Raspberry Pi 3B display and local/LAN notification hub for a home-lab mini rack.

`pi-hud` owns an **ST7735S 160×80 SPI display**. It shows system status by default
(hostname, temperature, CPU, RAM, service badges) and switches to persistent alert
screens when apps send messages — e.g. `pi-dns-sync` posting a `DNS Updated` alert.
Alerts stay pinned on the physical screen until cleared from a local web UI, and every
message is persisted in SQLite so it can be inspected later.

**Fast. Simple. Secure. Resource efficient.** — Native systemd service, single Uvicorn
worker, FastAPI + Jinja2 + a little vanilla JS. No React/Vue/Node/Tailwind, no Docker.

## Install

On the Raspberry Pi:

```bash
git clone https://github.com/atefalvi/pi-hud.git
cd pi-hud
sudo ./install.sh
```

The installer creates a venv, installs dependencies, sets up `/opt/pi-hud`,
`/etc/pi-hud/config.ini`, and `/var/lib/pi-hud/pi-hud.db`, installs and enables the
`pi-hud.service`, initializes the database, creates the first app token, and prints the
service status, local URL, and that token (shown **once** — copy it).

One-liner (clone + install):

```bash
git clone https://github.com/atefalvi/pi-hud.git && cd pi-hud && sudo ./install.sh
```

> Enable SPI first if you haven't: `sudo raspi-config` → Interface Options → SPI → reboot.

## Wiring (ST7735S 0.96" 160×80)

BCM numbering — these are the defaults in `config.ini` and match the proven
`pi-rack-hud` wiring. All of them are editable on the **Settings** page.

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

### Update / uninstall

```bash
sudo ./update.sh              # pull-in new code, migrate schema, restart
sudo ./uninstall.sh           # remove service + app (keeps the database)
sudo ./uninstall.sh --purge   # also delete the database
```

## Service commands

```bash
sudo systemctl status pi-hud
sudo systemctl restart pi-hud
journalctl -u pi-hud -n 100 --no-pager
```

## Web UI

Open `http://127.0.0.1:8765` (or `http://<PI_IP>:8765` in LAN mode). Pages: Dashboard,
Messages (+ detail), Tokens, Settings, Logs, API docs. The dashboard "Current display"
is the live rendered panel image.

## Sending messages

Apps authenticate with a bearer token (create one on the **Tokens** page) and POST to
`/api/v1/messages`:

```bash
curl -X POST http://127.0.0.1:8765/api/v1/messages \
  -H "Authorization: Bearer ph_xxx" -H "Content-Type: application/json" \
  -d '{"source":"pi-dns-sync","type":"success","title":"DNS Updated",
       "message":"Cloudflare A record updated.","pinned":true,"priority":6,"category":"dns",
       "metadata":{"host":"home.example.com","record_type":"A",
                   "previous_value":"203.0.113.42","updated_value":"198.51.100.27"}}'
```

`pi-dns-sync` same-Pi config: see [`examples/docker-compose.pi-dns-sync.yml`](examples/docker-compose.pi-dns-sync.yml).

## Configuration

Infrastructure settings live in `/etc/pi-hud/config.ini` (host/port, display pins, SPI,
refresh intervals) and require a restart. Live-tunable thresholds are edited on the
**Settings** page.

Default is local-only on `127.0.0.1`. To reach the web UI / API from other devices
(e.g. `http://192.168.x.x:8765`), enable LAN mode explicitly:

```ini
[api]
lan_mode = true
```

then `sudo systemctl restart pi-hud`. **Do not expose pi-hud to the public internet.**

See [`config.example.ini`](config.example.ini).

## Runtime layout

```
/opt/pi-hud                  application + venv
/etc/pi-hud/config.ini       configuration
/var/lib/pi-hud/pi-hud.db    SQLite database (WAL)
```

## Troubleshooting

**Panel shows random static / doesn't update** — run the display triage tool, which
drives the panel directly and reports each step:

```bash
sudo systemctl stop pi-hud
sudo PI_HUD_CONFIG=/etc/pi-hud/config.ini \
  /opt/pi-hud/.venv/bin/python -m pi_hud.display_test        # add --slow for 4MHz
sudo systemctl start pi-hud
```

You should see red → green → blue → white, then the boot screen. If nothing changes,
check the pins in `/etc/pi-hud/config.ini` against the Wiring table above (a stale config
from an older install may have wrong DC/RST/BL pins — fix them on the Settings page or in
the file) and confirm SPI is enabled. `curl http://127.0.0.1:8765/health` reports the display status
(`ok` / `unavailable`), and `journalctl -u pi-hud -n 50` shows driver errors.

**Can't reach the web UI from another device** — enable LAN mode (see Configuration).

## Development

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e . && pip install pytest httpx
PYTHONPATH=src python -m pytest tests/ -q      # 15 tests
```

The display driver imports `spidev`/`RPi.GPIO` lazily, so the app runs headless on a dev
machine (display disabled); the web UI and API work unchanged.

## Design & handoff docs

Design target is the DataDreamer Observatory direction (dark-first, hairline rules, ember
accent). Canonical visual reference: `agent-workspace/assets/pi-hud-final-mockups.html`.
Specs and build reports live under [`agent-workspace/`](agent-workspace/) — PRD, API, database
schema, driver optimization, security, and the WORKLOG / DECISIONS / TEST_REPORT / DESIGN_REVIEW.

## License

MIT — see [LICENSE](LICENSE).
