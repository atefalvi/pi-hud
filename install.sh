#!/usr/bin/env bash
# pi-hud installer. Native systemd service (no Docker). Run with sudo on the Pi.
set -euo pipefail

APP_DIR=/opt/pi-hud
CFG_DIR=/etc/pi-hud
DATA_DIR=/var/lib/pi-hud
LOG_DIR=/var/log/pi-hud
RUN_USER="${SUDO_USER:-$(whoami)}"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ $EUID -ne 0 ]]; then echo "Run with sudo."; exit 1; fi
echo "==> Installing pi-hud as service user: $RUN_USER"

echo "==> apt dependencies"
apt-get update -qq
apt-get install -y python3 python3-venv python3-pip python3-dev git curl fontconfig sqlite3
# Hardware GPIO lib (best-effort; harmless if the display is disabled)
apt-get install -y python3-rpi.gpio || echo "   (python3-rpi.gpio not installed; enable display later)"

if ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null && \
   ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null; then
  echo "!!  SPI does not appear to be enabled. Run 'sudo raspi-config' -> Interface -> SPI, then reboot."
fi

echo "==> Directories"
mkdir -p "$APP_DIR" "$CFG_DIR" "$DATA_DIR" "$LOG_DIR"

echo "==> Copying application to $APP_DIR"
cp -r "$SRC_DIR/src" "$SRC_DIR/pyproject.toml" "$SRC_DIR/requirements.txt" "$APP_DIR/"

echo "==> Config"
if [[ ! -f "$CFG_DIR/config.ini" ]]; then
  cp "$SRC_DIR/config.example.ini" "$CFG_DIR/config.ini"
  echo "   wrote $CFG_DIR/config.ini (local-only 127.0.0.1 by default)"
else
  echo "   $CFG_DIR/config.ini exists, leaving it"
fi

echo "==> Python venv + dependencies"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip
"$APP_DIR/.venv/bin/pip" install -q -e "$APP_DIR"
# Display hardware extras (optional; ignore failure on non-Pi)
"$APP_DIR/.venv/bin/pip" install -q spidev RPi.GPIO || echo "   (hardware extras skipped)"

echo "==> Permissions + groups"
chown -R "$RUN_USER":"$RUN_USER" "$APP_DIR" "$CFG_DIR" "$DATA_DIR" "$LOG_DIR"
usermod -aG spi,gpio "$RUN_USER" 2>/dev/null || true

echo "==> Initialize database + first token"
TOKEN=$(sudo -u "$RUN_USER" PI_HUD_CONFIG="$CFG_DIR/config.ini" \
  "$APP_DIR/.venv/bin/python" -c \
  "from pi_hud import config, db, auth; c=config.load(); db.init(c.get('database','path')); print(auth.ensure_first_token() or '')")

echo "==> systemd service"
sed "s/__USER__/$RUN_USER/g" "$SRC_DIR/systemd/pi-hud.service.template" \
  > /etc/systemd/system/pi-hud.service
systemctl daemon-reload
systemctl enable pi-hud
systemctl restart pi-hud
sleep 2

PORT=$(sed -n 's/^port *= *//p' "$CFG_DIR/config.ini" | head -1)
echo
echo "============================================================"
systemctl --no-pager status pi-hud | head -5 || true
echo "------------------------------------------------------------"
echo "health: $(curl -s "http://127.0.0.1:${PORT:-8765}/health" || echo unreachable)"
echo "pi-hud is running:  http://127.0.0.1:${PORT:-8765}"
echo "LAN access: set 'lan_mode = true' in $CFG_DIR/config.ini, then"
echo "            sudo systemctl restart pi-hud"
echo "Display triage: sudo systemctl stop pi-hud && sudo PI_HUD_CONFIG=$CFG_DIR/config.ini \\"
echo "            $APP_DIR/.venv/bin/python -m pi_hud.display_test"
if [[ -n "$TOKEN" ]]; then
  echo "First app token (shown ONCE — copy it now):"
  echo "   $TOKEN"
else
  echo "A token already existed; create more at /tokens."
fi
echo "============================================================"
