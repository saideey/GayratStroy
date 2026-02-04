"""
ERP Backup Server
- Runs pg_dump on schedule (daily at configured hour)
- Serves backup files via HTTP endpoints
- Auto-cleans old backups
"""

import os
import sys
import time
import glob
import gzip
import hashlib
import subprocess
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, send_file, jsonify, request, abort

# ============================================================
# Configuration
# ============================================================

BACKUP_DIR = os.getenv("BACKUP_DIR", "/backups")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "gayratstroy_db")
BACKUP_HOUR = int(os.getenv("BACKUP_HOUR", "0"))  # 0 = midnight
BACKUP_MINUTE = int(os.getenv("BACKUP_MINUTE", "0"))
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "1"))  # keep only latest
BACKUP_API_KEY = os.getenv("BACKUP_API_KEY", "erp-backup-secret-2026")
SERVER_PORT = int(os.getenv("BACKUP_SERVER_PORT", "8085"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("backup")

# Ensure backup directory exists
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# ============================================================
# Backup Logic
# ============================================================

def get_backup_filename():
    """Generate backup filename with current datetime."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M") + "_erp_backup.dump.gz"


def calculate_md5(filepath):
    """Calculate MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def run_backup():
    """Execute pg_dump and compress with gzip."""
    filename = get_backup_filename()
    filepath = os.path.join(BACKUP_DIR, filename)
    temp_path = filepath + ".tmp"

    logger.info(f"Starting backup: {filename}")
    logger.info(f"Database: {DB_NAME}@{DB_HOST}:{DB_PORT}")

    start_time = time.time()

    try:
        # Set password via environment
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD

        # Run pg_dump → gzip
        pg_dump_cmd = [
            "pg_dump",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", DB_NAME,
            "--format=custom",    # Custom format (most efficient)
            "--compress=6",       # Compression level
            "--no-owner",         # Don't include ownership
            "--no-privileges",    # Don't include privileges
            "--verbose"
        ]

        with open(temp_path, "wb") as outfile:
            result = subprocess.run(
                pg_dump_cmd,
                stdout=outfile,
                stderr=subprocess.PIPE,
                env=env,
                timeout=600  # 10 minute timeout
            )

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            logger.error(f"pg_dump failed: {stderr}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None

        # Rename temp to final
        os.rename(temp_path, filepath)

        elapsed = time.time() - start_time
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        md5 = calculate_md5(filepath)

        logger.info(f"✅ Backup completed: {filename}")
        logger.info(f"   Size: {size_mb:.2f} MB | Time: {elapsed:.1f}s | MD5: {md5}")

        # Clean old backups
        cleanup_old_backups()

        return filepath

    except subprocess.TimeoutExpired:
        logger.error("pg_dump timed out (>10 minutes)")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None


def cleanup_old_backups():
    """Remove all old backups, keep only MAX_BACKUPS (default=1) most recent."""
    pattern = os.path.join(BACKUP_DIR, "*_erp_backup.dump*")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

    removed = 0
    if len(files) > MAX_BACKUPS:
        for old_file in files[MAX_BACKUPS:]:
            try:
                os.remove(old_file)
                removed += 1
                logger.info(f"🗑️  Eski backup o'chirildi: {os.path.basename(old_file)}")
            except Exception as e:
                logger.error(f"Failed to remove {old_file}: {e}")
    
    if removed > 0:
        logger.info(f"🗑️  Jami {removed} ta eski backup o'chirildi. Serverda faqat {MAX_BACKUPS} ta qoldi.")


def get_latest_backup():
    """Get the most recent backup file path."""
    pattern = os.path.join(BACKUP_DIR, "*_erp_backup.dump*")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def get_all_backups():
    """Get list of all backup files with metadata."""
    pattern = os.path.join(BACKUP_DIR, "*_erp_backup.dump*")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

    result = []
    for f in files:
        stat = os.stat(f)
        result.append({
            "filename": os.path.basename(f),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "md5": calculate_md5(f)
        })
    return result


# ============================================================
# Scheduler - runs backup daily
# ============================================================

def scheduler_loop():
    """Simple scheduler that runs backup at configured time."""
    logger.info(f"Scheduler started. Backup time: {BACKUP_HOUR:02d}:{BACKUP_MINUTE:02d}")

    # Run initial backup on startup if no backups exist
    if not get_latest_backup():
        logger.info("No existing backups found. Running initial backup...")
        run_backup()

    while True:
        now = datetime.now()
        # Calculate next backup time
        target = now.replace(hour=BACKUP_HOUR, minute=BACKUP_MINUTE, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        hours_left = wait_seconds / 3600

        logger.info(f"⏰ Next backup at {target.strftime('%Y-%m-%d %H:%M')} ({hours_left:.1f} hours)")

        # Sleep until backup time (check every 30 seconds for accuracy)
        while datetime.now() < target:
            time.sleep(30)

        # Run backup
        run_backup()

        # Small delay to prevent double-run
        time.sleep(60)


# ============================================================
# Flask API
# ============================================================

app = Flask(__name__)


def check_api_key():
    """Verify API key from request."""
    key = request.headers.get("X-Backup-Key") or request.args.get("key")
    if key != BACKUP_API_KEY:
        abort(403, description="Invalid API key")


@app.route("/health", methods=["GET"])
def health():
    """Health check - no auth required."""
    latest = get_latest_backup()
    return jsonify({
        "status": "ok",
        "service": "erp-backup",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "has_backups": latest is not None
    })


@app.route("/backup-info", methods=["GET"])
def backup_info():
    """Get info about the latest backup."""
    check_api_key()

    latest = get_latest_backup()
    if not latest:
        return jsonify({
            "success": False,
            "error": "No backups available"
        }), 404

    stat = os.stat(latest)
    return jsonify({
        "success": True,
        "filename": os.path.basename(latest),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "md5": calculate_md5(latest),
        "database": DB_NAME,
        "total_backups": len(get_all_backups())
    })


@app.route("/latest-backup", methods=["GET"])
def download_latest():
    """Download the latest backup file."""
    check_api_key()

    latest = get_latest_backup()
    if not latest:
        return jsonify({
            "success": False,
            "error": "No backups available"
        }), 404

    filename = os.path.basename(latest)
    logger.info(f"📥 Backup download requested: {filename}")

    return send_file(
        latest,
        as_attachment=True,
        download_name=filename,
        mimetype="application/octet-stream"
    )


@app.route("/backup-list", methods=["GET"])
def backup_list():
    """List all available backups."""
    check_api_key()

    backups = get_all_backups()
    return jsonify({
        "success": True,
        "count": len(backups),
        "backups": backups
    })


@app.route("/download/<filename>", methods=["GET"])
def download_specific(filename):
    """Download a specific backup by filename."""
    check_api_key()

    filepath = os.path.join(BACKUP_DIR, filename)

    # Security: prevent directory traversal
    if ".." in filename or "/" in filename:
        abort(400, description="Invalid filename")

    if not os.path.exists(filepath):
        return jsonify({
            "success": False,
            "error": f"Backup not found: {filename}"
        }), 404

    logger.info(f"📥 Specific backup download: {filename}")

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype="application/octet-stream"
    )


@app.route("/run-backup", methods=["POST"])
def trigger_backup():
    """Manually trigger a backup."""
    check_api_key()

    logger.info("🔧 Manual backup triggered via API")
    filepath = run_backup()

    if filepath:
        stat = os.stat(filepath)
        return jsonify({
            "success": True,
            "filename": os.path.basename(filepath),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "md5": calculate_md5(filepath)
        })
    else:
        return jsonify({
            "success": False,
            "error": "Backup failed. Check server logs."
        }), 500


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("  ERP Backup Service")
    logger.info(f"  Database: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    logger.info(f"  Backup dir: {BACKUP_DIR}")
    logger.info(f"  Schedule: daily at {BACKUP_HOUR:02d}:{BACKUP_MINUTE:02d}")
    logger.info(f"  Max backups: {MAX_BACKUPS}")
    logger.info(f"  API port: {SERVER_PORT}")
    logger.info("=" * 50)

    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()

    # Start Flask server
    app.run(
        host="0.0.0.0",
        port=SERVER_PORT,
        debug=False,
        use_reloader=False
    )
