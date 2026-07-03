# Installation and Deployment

## Install paths

```text
/opt/pi-hud                  app
/etc/pi-hud/config.ini       config
/var/lib/pi-hud/pi-hud.db    SQLite database
/var/log/pi-hud/             optional logs
```

## Installer responsibilities

`install.sh` must:

1. Install apt dependencies.
2. Enable SPI reminder/check.
3. Create `pi-hud` system user if needed.
4. Create install/config/data directories.
5. Create Python venv.
6. Install Python dependencies.
7. Copy service template.
8. Initialize database.
9. Create first admin/app token.
10. Enable and start systemd service.
11. Print service status and URL.

## Apt dependencies

```bash
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  git \
  curl \
  fontconfig \
  sqlite3
```

Hardware dependencies may require:

```bash
sudo apt install -y python3-rpi.gpio
```

## Systemd service

```ini
[Unit]
Description=pi-hud display and notification hub
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/pi-hud
ExecStart=/opt/pi-hud/.venv/bin/python -m pi_hud.main
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## Commands

```bash
sudo systemctl status pi-hud
sudo systemctl restart pi-hud
journalctl -u pi-hud -n 100 --no-pager
```

## Update script

`update.sh`:

1. Pull latest code.
2. Activate venv.
3. Install requirements.
4. Run migrations.
5. Restart service.
