#!/bin/bash
# ============================================
# WhoIsOnFirst - Docker Entrypoint Script
# ============================================
# Simple entrypoint that checks write access
# and provides helpful error messages
# ============================================

set -e

DATA_DIR="/app/data"
DB_FILE="$DATA_DIR/whoisonfirst.db"

echo "WhoIsOnFirst starting..."
echo "Running as UID: $(id -u), GID: $(id -g)"

# Check if data directory is writable
if [ ! -w "$DATA_DIR" ]; then
    echo ""
    echo "ERROR: Data directory ($DATA_DIR) is not writable!"
    echo ""
    echo "Fix options:"
    echo "  Docker/Podman:"
    echo "    docker exec -u 0 <container> chown -R whoisonfirst:root /app/data"
    echo "    docker exec -u 0 <container> chmod -R g+rwX /app/data"
    echo ""
    echo "  OpenShift (run as init container):"
    echo "    chown -R 1001:0 /app/data && chmod -R g+rwX /app/data"
    echo ""
    exit 1
fi

# One-time rename of a pre-WOF-37 database (whoseonfirst.db -> whoisonfirst.db).
# Must run before migrations and the app's first-boot auto-seed.
/app/migrate-db-filename.sh "$DATA_DIR"

# Check if database file is writable (if it exists)
if [ -f "$DB_FILE" ] && [ ! -w "$DB_FILE" ]; then
    echo ""
    echo "ERROR: Database file ($DB_FILE) is not writable!"
    echo ""
    echo "Fix: docker exec -u 0 <container> chmod g+rw $DB_FILE"
    echo ""
    exit 1
fi

echo "Data directory is writable - OK"

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Start the application
echo "Starting WhoIsOnFirst application..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
