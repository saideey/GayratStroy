#!/bin/bash
set -e

echo "🔄 Metall Basa API Starting..."
echo "================================"

# Wait for PostgreSQL to be available (port open)
echo "⏳ Waiting for PostgreSQL port to be available..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if pg_isready -h db -p 5432 -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL port is open!"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "   Attempt $retry_count/$max_retries..."
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ PostgreSQL is not available after $max_retries attempts"
    exit 1
fi

# Give PostgreSQL a moment to fully initialize
sleep 3

# Test database connection with retry logic
echo "🔄 Testing database connection..."
max_db_retries=5
db_retry_count=0
db_connected=false

while [ $db_retry_count -lt $max_db_retries ]; do
    python -c "
import os
import sys
from sqlalchemy import create_engine, text

database_url = os.getenv('DATABASE_URL')
try:
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful!')
    sys.exit(0)
except Exception as e:
    print(f'⚠️  Connection attempt failed: {e}')
    sys.exit(1)
" && db_connected=true && break

    db_retry_count=$((db_retry_count + 1))
    echo "   Retry $db_retry_count/$max_db_retries in 5 seconds..."
    sleep 5
done

if [ "$db_connected" = false ]; then
    echo "❌ Could not connect to database after $max_db_retries attempts"
    echo "   Please check database credentials and run fix_db_password.sh"
    exit 1
fi

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head || {
    echo "⚠️  Migration failed, but continuing..."
}

# Seed database
echo "🔄 Seeding database..."
python -c "
from database.seed import seed_all
from database import db
try:
    seed_all(db.get_session_direct())
    print('✅ Database seeded!')
except Exception as e:
    print(f'⚠️  Seeding skipped: {e}')
" || true

echo ""
echo "🚀 Starting Uvicorn server..."
echo "================================"
exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload
