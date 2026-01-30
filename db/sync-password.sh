#!/bin/bash
# Password sync - background da ishlaydi
set -e

sync_password() {
    # PostgreSQL to'liq ishga tushguncha kutish
    echo "⏳ Waiting for PostgreSQL to accept connections..."
    until pg_isready -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; do
        sleep 1
    done
    
    sleep 2  # Extra wait for full initialization
    
    echo "🔄 Syncing password for user ${POSTGRES_USER:-postgres}..."
    
    # Parolni yangilash
    psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}" -c \
        "ALTER USER ${POSTGRES_USER:-postgres} WITH PASSWORD '${POSTGRES_PASSWORD:-postgres}';" \
        > /dev/null 2>&1 || true
    
    echo "✅ Password sync completed!"
}

# Background da ishga tushirish
sync_password &
