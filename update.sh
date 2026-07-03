#!/usr/bin/env bash
# Update an installed pi-hud from this source tree.
set -euo pipefail
APP_DIR=/opt/pi-hud
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ $EUID -ne 0 ]]; then echo "Run with sudo."; exit 1; fi
RUN_USER=$(stat -c '%U' "$APP_DIR" 2>/dev/null || echo "${SUDO_USER:-pi}")

echo "==> Copying updated code"
cp -r "$SRC_DIR/src" "$SRC_DIR/pyproject.toml" "$SRC_DIR/requirements.txt" "$APP_DIR/"
chown -R "$RUN_USER":"$RUN_USER" "$APP_DIR"

echo "==> Updating dependencies"
"$APP_DIR/.venv/bin/pip" install -q -e "$APP_DIR"

echo "==> Applying schema (idempotent) + restart"
sudo -u "$RUN_USER" PI_HUD_CONFIG=/etc/pi-hud/config.ini \
  "$APP_DIR/.venv/bin/python" -c \
  "from pi_hud import config, db; c=config.load(); db.init(c.get('database','path'))"
systemctl restart pi-hud
systemctl --no-pager status pi-hud | head -5
