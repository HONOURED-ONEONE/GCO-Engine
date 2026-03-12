#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "Starting backup to $BACKUP_DIR..."

# 1. DB Backups (governance, kpi, policy, ot)
# For SQLite
if [ -f "governance.db" ]; then cp "governance.db" "$BACKUP_DIR/governance.sql"; fi
if [ -f "kpi.db" ]; then cp "kpi.db" "$BACKUP_DIR/kpi.sql"; fi
if [ -f "policy.db" ]; then cp "policy.db" "$BACKUP_DIR/policy.sql"; fi
if [ -f "ot.db" ]; then cp "ot.db" "$BACKUP_DIR/ot.sql"; fi

# If docker is running and postgres is being used, we could do pg_dump
if docker ps | grep -q gco-engine-db; then
    echo "Postgres detected, performing pg_dump..."
    docker exec gco-engine-db pg_dump -U gco_admin gco_engine > "$BACKUP_DIR/gco_engine_full.sql"
fi

# 2. Evidence Artifacts
if [ -d "evidence" ]; then
    tar -czf "$BACKUP_DIR/evidence.tar.gz" evidence/
fi

# 3. Data JSON files (as fallback)
if [ -d "data" ]; then
    tar -czf "$BACKUP_DIR/data_json.tar.gz" data/
fi

# 4. Manifest and Checksums
cat <<EOF > "$BACKUP_DIR/manifest.json"
{
  "timestamp": "$TIMESTAMP",
  "version": "1.0",
  "type": "full_backup"
}
EOF

cd "$BACKUP_DIR"
find . -type f -not -name "checksums.txt" -exec sha256sum {} + > "checksums.txt"
cd - > /dev/null

echo "Backup complete: $BACKUP_DIR"
