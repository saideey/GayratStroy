#!/bin/bash
set -e

echo "================================================"
echo "  ERP Backup Service Starting..."
echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Backup schedule: Daily at ${BACKUP_HOUR:-00}:00"
echo "  Max backups kept: ${MAX_BACKUPS:-30}"
echo "================================================"

# Run backup server
exec python -u backup_server.py
