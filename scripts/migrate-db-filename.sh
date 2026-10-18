#!/bin/bash
# ============================================
# WhoIsOnFirst - one-time DB filename migration (WOF-37)
# ============================================
# Renames whoseonfirst.db (plus its SQLite -wal/-shm sidecars) to
# whoisonfirst.db inside the data directory. The entrypoint runs this
# BEFORE migrations and before the app's first-boot auto-seed, so an
# existing database is moved in place and never seeded over.
#
#   old only  -> moved
#   new only  -> nothing to do
#   both      -> untouched, WARNING (needs a human to pick one)
#   neither   -> nothing to do (fresh install)
#
# Usage: migrate-db-filename.sh [DATA_DIR]   (default /app/data)
# ============================================

set -euo pipefail

DATA_DIR="${1:-/app/data}"
OLD="$DATA_DIR/whoseonfirst.db"
NEW="$DATA_DIR/whoisonfirst.db"

if [ ! -e "$OLD" ]; then
    exit 0
fi

if [ -e "$NEW" ]; then
    echo "WARNING: both $OLD and $NEW exist; leaving both untouched."
    echo "WARNING: the app uses $NEW. Remove or archive the old file once verified."
    exit 0
fi

for suffix in "" "-wal" "-shm"; do
    if [ -e "$OLD$suffix" ]; then
        mv "$OLD$suffix" "$NEW$suffix"
    fi
done

echo "Renamed database file: whoseonfirst.db -> whoisonfirst.db"
