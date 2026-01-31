#!/bin/bash
set -e

# =====================================================
# PostgreSQL Entrypoint Wrapper
# Password sync va pg_hba.conf boshqaruvi
# =====================================================

sync_password() {
    echo "⏳ [DB] Waiting for PostgreSQL to start..."
    
    # PostgreSQL tayyor bo'lguncha kutish (max 60 sekund)
    local count=0
    while [ $count -lt 60 ]; do
        if pg_isready -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; then
            break
        fi
        sleep 1
        count=$((count + 1))
    done
    
    if [ $count -ge 60 ]; then
        echo "⚠️ [DB] PostgreSQL did not start in time"
        return 1
    fi
    
    sleep 2
    
    echo "🔄 [DB] Syncing password for user: ${POSTGRES_USER:-postgres}"
    
    # Trust rejimida parolni yangilash
    psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}" -c \
        "ALTER USER ${POSTGRES_USER:-postgres} WITH PASSWORD '${POSTGRES_PASSWORD:-postgres}';" \
        2>/dev/null && echo "✅ [DB] Password synced successfully!" \
        || echo "⚠️ [DB] Password sync skipped (may already be set)"
}

# Background da password sync
sync_password &

# Original PostgreSQL entrypoint
exec docker-entrypoint.sh "$@"
