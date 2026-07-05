#!/bin/sh
# Denná záloha dát VORU: clients/ (konfigurácie, databázy, prílohy)
# + webapp.db (účty). Drží posledných 14 záloh v /root/backups.
#
# Cron: 45 3 * * * /root/TMB/scripts/backup.sh >> /root/TMB/agent.log 2>&1
#
# Odporúčanie: /root/backups pravidelne synchronizujte aj mimo servera
# (Hetzner Storage Box, rsync na iný stroj...), aby ste prežili výpadok disku.

set -eu

SRC_DIR="${SRC_DIR:-/root/TMB}"
DEST="${DEST:-/root/backups}"
KEEP="${KEEP:-14}"

mkdir -p "$DEST"
STAMP=$(date +%Y%m%d-%H%M)
tar -czf "$DEST/voru-$STAMP.tar.gz" \
    -C "$SRC_DIR" \
    $( [ -d "$SRC_DIR/clients" ] && echo clients ) \
    $( [ -f "$SRC_DIR/webapp.db" ] && echo webapp.db ) \
    $( [ -f "$SRC_DIR/.env.master" ] && echo .env.master )

# zmaž zálohy nad limit (najstaršie prvé)
ls -1t "$DEST"/voru-*.tar.gz 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r f; do
    rm -f "$f"
done

echo "Záloha OK: $DEST/voru-$STAMP.tar.gz"
