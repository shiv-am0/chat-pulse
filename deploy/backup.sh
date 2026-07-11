#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/chatpulse/backups}"
DB_NAME="${DB_NAME:-chatpulse}"
DB_USER="${DB_USER:-admin}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "${DB_HOST:-localhost}" \
    -p "${DB_PORT:-5432}" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    | gzip > "$FILENAME"

echo "Backup created: $FILENAME ($(du -h "$FILENAME" | cut -f1))"

find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
echo "Removed backups older than $RETENTION_DAYS days"
