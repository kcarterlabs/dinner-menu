#!/bin/bash
# Backup MongoDB data to compressed archive

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mongodb-backup-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "🔄 Creating MongoDB backup..."
echo "Source: ./data/mongodb"
echo "Target: $BACKUP_FILE"

# Create compressed backup
tar -czf "$BACKUP_FILE" data/mongodb/

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup complete: $BACKUP_FILE ($SIZE)"
    
    # Keep only last 10 backups
    ls -t "$BACKUP_DIR"/mongodb-backup-*.tar.gz | tail -n +11 | xargs -r rm
    echo "📦 Old backups cleaned up (keeping last 10)"
else
    echo "❌ Backup failed"
    exit 1
fi
