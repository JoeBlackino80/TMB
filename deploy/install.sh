#!/usr/bin/env bash
# Nasadenie ValidFlight na VPS (Debian/Ubuntu, spúšťať ako root z adresára repa):
#   sudo bash deploy/install.sh [používateľ]
# Predpoklady: python3-venv; vyplnený .env (DUFFEL_API_KEY, SMTP, Stripe...).
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="${1:-$(stat -c %U "$APP_DIR")}"

echo "== ValidFlight install: $APP_DIR (user: $APP_USER)"

[ -f "$APP_DIR/.env" ] || { echo "CHYBA: chýba $APP_DIR/.env (skopíruj .env.example a vyplň)"; exit 1; }

python3 -m venv "$APP_DIR/.venv" 2>/dev/null || true
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements-onward.txt"

for unit in validflight.service validflight-expire.service validflight-expire.timer; do
    sed -e "s|__APP_DIR__|$APP_DIR|g" -e "s|__APP_USER__|$APP_USER|g" \
        "$APP_DIR/deploy/$unit" > "/etc/systemd/system/$unit"
done
systemctl daemon-reload
systemctl enable --now validflight.service validflight-expire.timer

echo "== Hotovo. Kontrola:"
systemctl --no-pager status validflight.service | head -5
echo "Web beží na 127.0.0.1:8100 — pred ním nastav Caddy alebo nginx (pozri deploy/)."
