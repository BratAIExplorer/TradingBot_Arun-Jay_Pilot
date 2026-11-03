#!/bin/bash
# =============================================================================
# Database backup — TradingBot VPS
# =============================================================================
# Run via tradingbot-backup.timer (installed by setup.sh). Can also be run
# manually: bash backup_db.sh
#
# Guardrails:
#   - Uses `sqlite3 .backup`, not `cp`, so a live write mid-backup can't
#     produce a torn/corrupt copy (cp on an open SQLite file can).
#   - Never touches or deletes the source database — read-only against it.
#   - Backups are additive only: this script deletes old *backup copies*
#     past the retention window, never the live database.
#   - Fails loudly (set -e) rather than silently skipping a backup.
# =============================================================================
set -e

APP_DIR="/opt/tradingbot"
DB_DIR="$APP_DIR/database"
BACKUP_DIR="$APP_DIR/backups"
RETENTION_DAYS=30
STAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

for db in trades.db scan_results.db order_attempts.db; do
    src="$DB_DIR/$db"
    [ -f "$src" ] || continue
    dst="$BACKUP_DIR/${db%.db}_${STAMP}.db"
    sqlite3 "$src" ".backup '$dst'"
    echo "Backed up $db -> $dst"
done

# Retention: delete backup copies older than RETENTION_DAYS. Only matches
# files inside BACKUP_DIR with the _<timestamp>.db suffix this script writes
# — never touches $DB_DIR.
find "$BACKUP_DIR" -maxdepth 1 -name "*_*.db" -mtime "+$RETENTION_DAYS" -delete

echo "Backup complete. $(ls "$BACKUP_DIR" | wc -l) backup files retained."
echo "NOTE: this is local-disk backup only. For real disaster recovery, copy"
echo "$BACKUP_DIR off-box periodically (scp/rsync to another machine)."
