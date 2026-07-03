#!/usr/bin/env bash
# Remove pi-hud. Keeps the database unless --purge is given.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo "Run with sudo."; exit 1; fi

echo "==> Stopping service"
systemctl disable --now pi-hud 2>/dev/null || true
rm -f /etc/systemd/system/pi-hud.service
systemctl daemon-reload

echo "==> Removing app + config"
rm -rf /opt/pi-hud /etc/pi-hud

if [[ "${1:-}" == "--purge" ]]; then
  echo "==> Purging database and logs"
  rm -rf /var/lib/pi-hud /var/log/pi-hud
else
  echo "   Kept /var/lib/pi-hud (use --purge to delete the database)."
fi
echo "Done."
