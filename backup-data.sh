#!/bin/bash

# Media Downloader Data Backup Script
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="media_downloader_backup_${TIMESTAMP}.tar.gz"

echo "💾 Creating backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create compressed backup of data directory
tar -czf "$BACKUP_DIR/$BACKUP_FILE" data/

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_FILE"
echo "📊 Backup size: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t media_downloader_backup_*.tar.gz | tail -n +11 | xargs rm -f 2>/dev/null || true
cd ..

echo "🗂️ Total backups: $(ls "$BACKUP_DIR"/media_downloader_backup_*.tar.gz 2>/dev/null | wc -l)"
