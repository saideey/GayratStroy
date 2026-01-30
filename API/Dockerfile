FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_ROOT_USER_ACTION=ignore

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    tzdata \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set timezone
ENV TZ=Asia/Tashkent

# Install specific pip version that works
RUN python -m pip install --upgrade "pip>=23.0,<24.0"

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run startup command directly
CMD ["bash", "-c", "\
    echo '🔄 Waiting for PostgreSQL...' && \
    while ! pg_isready -h db -p 5432 -U postgres > /dev/null 2>&1; do \
        echo '⏳ Waiting...' && sleep 2; \
    done && \
    echo '✅ PostgreSQL is ready!' && \
    sleep 3 && \
    echo '🔄 Running migrations...' && \
    alembic upgrade head || true && \
    echo '🔄 Seeding database...' && \
    python -c 'from database.seed import seed_all; from database import db; seed_all(db.get_session_direct())' || true && \
    echo '🚀 Starting server...' && \
    exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload \
"]
