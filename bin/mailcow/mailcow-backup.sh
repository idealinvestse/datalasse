#!/bin/bash
# mailcow-backup.sh — Backup av mailcow-konfiguration + vmail-data
# Körs hourly via cron → /root/backups/mailcow/<timestamp>/
#
# Innehåll:
#   - mailcow config (nginx, postfix, rspamd, dovecot, etc.)
#   - vmail-data (alla mailboxar)
#   - mailcow.env
#   - SSL-certifikat
#   - Custom postfix (sasl_passwd)
#
# Kräver root (för att läsa /opt/mailcow/).

set -euo pipefail

BACKUP_ROOT="/root/backups/mailcow"
TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
LOG="/var/log/mailcow-backup.log"
MAX_BACKUPS=24  # Behåll 24 senaste (1 dygn om hourly)

mkdir -p "$BACKUP_DIR"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting mailcow backup → $BACKUP_DIR" | tee -a "$LOG"

# 1. mailcow config
if [ -d /opt/mailcow/data/conf ]; then
  echo "  [conf] /opt/mailcow/data/conf/..." | tee -a "$LOG"
  tar -czf "$BACKUP_DIR/conf.tar.gz" -C /opt/mailcow/data conf/ 2>&1 | head -3
fi

# 2. vmail-data (alla mailboxar) — i Docker-volymen
VMAIL_VOL="/var/lib/docker/volumes/mailcowdockerized_vmail-vol-1/_data"
if [ -d "$VMAIL_VOL" ]; then
  echo "  [vmail] $VMAIL_VOL/..." | tee -a "$LOG"
  tar -czf "$BACKUP_DIR/vmail.tar.gz" -C "$VMAIL_VOL" . 2>&1 | head -3
fi

# 2b. vmail-index (Dovecot fulltext-index)
VMAIL_INDEX_VOL="/var/lib/docker/volumes/mailcowdockerized_vmail-index-vol-1/_data"
if [ -d "$VMAIL_INDEX_VOL" ]; then
  echo "  [vmail-index] $VMAIL_INDEX_VOL/..." | tee -a "$LOG"
  tar -czf "$BACKUP_DIR/vmail-index.tar.gz" -C "$VMAIL_INDEX_VOL" . 2>&1 | head -3
fi

# 3. mailcow.env
if [ -f /opt/mailcow/mailcow.conf ]; then
  echo "  [mailcow.conf]" | tee -a "$LOG"
  cp /opt/mailcow/mailcow.conf "$BACKUP_DIR/mailcow.conf"
fi

# 4. SSL-cert
if [ -d /opt/mailcow/data/assets/ssl ]; then
  echo "  [ssl certs]" | tee -a "$LOG"
  tar -czf "$BACKUP_DIR/ssl.tar.gz" -C /opt/mailcow/data/assets ssl/ 2>&1 | head -3
fi

# 5. Custom postfix (sasl_passwd)
if [ -d /opt/mailcow/data/conf/postfix/custom ]; then
  echo "  [postfix custom]" | tee -a "$LOG"
  tar -czf "$BACKUP_DIR/postfix-custom.tar.gz" -C /opt/mailcow/data/conf/postfix custom/ 2>&1 | head -3
fi

# 6. Metadata
cat > "$BACKUP_DIR/META.json" << META_EOF
{
  "timestamp": "$TIMESTAMP",
  "size_bytes": $(du -sb "$BACKUP_DIR" | awk '{print $1}'),
  "files": $(ls "$BACKUP_DIR" | wc -l),
  "hostname": "$(hostname)",
  "ip": "$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo unknown)",
  "mailcow_version": "$(grep VERSION /opt/mailcow/mailcow.conf 2>/dev/null | cut -d= -f2 | tr -d '"' || echo unknown)"
}
META_EOF

# 7. Cleanup gamla backups
BACKUP_COUNT=$(ls -1d "$BACKUP_ROOT"/*/ 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
  OLD=$(ls -1dt "$BACKUP_ROOT"/*/ | tail -n +$((MAX_BACKUPS + 1)))
  for d in $OLD; do
    rm -rf "$d"
  done
  echo "  [cleanup] Removed $((BACKUP_COUNT - MAX_BACKUPS)) old backup(s)" | tee -a "$LOG"
fi

# 8. Sammanfattning
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | awk '{print $1}')
TOTAL_BACKUPS=$(ls -1d "$BACKUP_ROOT"/*/ 2>/dev/null | wc -l)
TOTAL_DISK=$(du -sh "$BACKUP_ROOT" 2>/dev/null | awk '{print $1}')
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Done: $BACKUP_DIR ($TOTAL_SIZE, total: $TOTAL_BACKUPS backups, $TOTAL_DISK)" | tee -a "$LOG"
