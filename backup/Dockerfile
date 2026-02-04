FROM python:3.11-slim

# Install PostgreSQL client for pg_dump (without specific version)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir flask gunicorn apscheduler

WORKDIR /app

# Create backup directory
RUN mkdir -p /backups

COPY backup_server.py /app/
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 8085

ENTRYPOINT ["/app/entrypoint.sh"]