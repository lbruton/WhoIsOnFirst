#!/bin/bash
# ============================================
# WhoIsOnFirst - Database Backup & Restore
# ============================================
# Simple script for backing up and restoring
# the SQLite database for deployment transfers
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CONTAINER_NAME="${CONTAINER_NAME:-whoisonfirst-dev}"
CONTAINER_DB_PATH="/app/data/whoisonfirst.db"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Detect container runtime
detect_runtime() {
    if command -v podman &> /dev/null && podman ps &> /dev/null; then
        echo "podman"
    elif command -v docker &> /dev/null && docker ps &> /dev/null; then
        echo "docker"
    else
        echo ""
    fi
}

backup_database() {
    print_header "Database Backup"

    RUNTIME=$(detect_runtime)
    if [[ -z "$RUNTIME" ]]; then
        print_error "Neither Docker nor Podman available/running"
        exit 1
    fi
    print_info "Using: $RUNTIME"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    BACKUP_FILE="$BACKUP_DIR/whoisonfirst-$TIMESTAMP.db"

    # Check if container is running
    if $RUNTIME ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_info "Container '$CONTAINER_NAME' is running"
        print_warning "Stopping container for safe backup..."
        $RUNTIME stop "$CONTAINER_NAME"
        RESTART_AFTER=true
    else
        print_info "Container '$CONTAINER_NAME' is not running"
        RESTART_AFTER=false
    fi

    # Copy database from container/volume
    if $RUNTIME cp "$CONTAINER_NAME:$CONTAINER_DB_PATH" "$BACKUP_FILE" 2>/dev/null; then
        print_success "Database backed up to: $BACKUP_FILE"
        ls -lh "$BACKUP_FILE"
    else
        # Try from named volume (for dev setup)
        print_info "Trying to backup from named volume..."
        VOLUME_PATH=$($RUNTIME volume inspect whoisonfirst-dev-db --format '{{.Mountpoint}}' 2>/dev/null || echo "")
        if [[ -n "$VOLUME_PATH" && -f "$VOLUME_PATH/whoisonfirst.db" ]]; then
            cp "$VOLUME_PATH/whoisonfirst.db" "$BACKUP_FILE"
            print_success "Database backed up from volume to: $BACKUP_FILE"
        else
            print_error "Could not locate database file"
            exit 1
        fi
    fi

    # Restart container if it was running
    if [[ "$RESTART_AFTER" == "true" ]]; then
        print_info "Restarting container..."
        $RUNTIME start "$CONTAINER_NAME"
        print_success "Container restarted"
    fi

    # Also backup .env if it exists
    if [[ -f ".env" ]]; then
        cp ".env" "$BACKUP_DIR/env-$TIMESTAMP.backup"
        print_success "Environment file backed up to: $BACKUP_DIR/env-$TIMESTAMP.backup"
    fi

    echo ""
    print_success "Backup complete!"
    print_info "Files to include in deployment package:"
    echo "  - $BACKUP_FILE"
    [[ -f "$BACKUP_DIR/env-$TIMESTAMP.backup" ]] && echo "  - $BACKUP_DIR/env-$TIMESTAMP.backup"
}

restore_database() {
    print_header "Database Restore"

    if [[ -z "$1" ]]; then
        print_error "Usage: $0 restore <backup_file.db>"
        echo ""
        echo "Available backups:"
        ls -la "$BACKUP_DIR"/*.db 2>/dev/null || echo "  No backups found in $BACKUP_DIR/"
        exit 1
    fi

    BACKUP_FILE="$1"

    if [[ ! -f "$BACKUP_FILE" ]]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    RUNTIME=$(detect_runtime)
    if [[ -z "$RUNTIME" ]]; then
        print_error "Neither Docker nor Podman available/running"
        exit 1
    fi
    print_info "Using: $RUNTIME"

    # Stop container if running
    if $RUNTIME ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_warning "Stopping container for restore..."
        $RUNTIME stop "$CONTAINER_NAME"
        RESTART_AFTER=true
    else
        RESTART_AFTER=false
    fi

    # Restore database
    print_info "Restoring database from: $BACKUP_FILE"

    # Try direct copy first
    if $RUNTIME cp "$BACKUP_FILE" "$CONTAINER_NAME:$CONTAINER_DB_PATH" 2>/dev/null; then
        print_success "Database restored to container"
        # Fix permissions after copy
        fix_container_permissions "$RUNTIME"
    else
        # Try named volume
        VOLUME_PATH=$($RUNTIME volume inspect whoisonfirst-dev-db --format '{{.Mountpoint}}' 2>/dev/null || echo "")
        if [[ -n "$VOLUME_PATH" ]]; then
            cp "$BACKUP_FILE" "$VOLUME_PATH/whoisonfirst.db"
            # Fix permissions on volume - make world-writable for OpenShift compatibility
            chmod 666 "$VOLUME_PATH/whoisonfirst.db" 2>/dev/null || true
            print_success "Database restored to volume"
        else
            # Create data directory and copy
            mkdir -p "./data"
            cp "$BACKUP_FILE" "./data/whoisonfirst.db"
            # Make world-writable for OpenShift arbitrary UID compatibility
            chmod 666 "./data/whoisonfirst.db"
            chmod 777 "./data"
            print_success "Database restored to ./data/whoisonfirst.db"
            print_info "Make sure your docker-compose.yml mounts ./data:/app/data"
        fi
    fi

    # Restart container
    if [[ "$RESTART_AFTER" == "true" ]]; then
        print_info "Restarting container..."
        $RUNTIME start "$CONTAINER_NAME"
        # Fix permissions after restart (container user now exists)
        fix_container_permissions "$RUNTIME"
        print_success "Container restarted"
    fi

    echo ""
    print_success "Restore complete!"
}

fix_container_permissions() {
    local RUNTIME="$1"
    print_info "Fixing database permissions..."

    # Try to fix ownership to whoisonfirst user (Docker Compose scenario)
    if $RUNTIME exec -u 0 "$CONTAINER_NAME" chown whoisonfirst:whoisonfirst /app/data /app/data/whoisonfirst.db 2>/dev/null; then
        print_success "Permissions fixed (whoisonfirst user)"
    # Fallback: make world-writable (OpenShift arbitrary UID scenario)
    elif $RUNTIME exec -u 0 "$CONTAINER_NAME" chmod -R 777 /app/data 2>/dev/null; then
        print_success "Permissions fixed (world-writable for OpenShift)"
    else
        print_warning "Could not fix permissions automatically"
        print_info "If you see 'readonly database' errors, run:"
        echo "  $RUNTIME exec -u 0 $CONTAINER_NAME chown -R whoisonfirst:whoisonfirst /app/data"
    fi
}

create_deployment_package() {
    print_header "Create Deployment Package"

    PACKAGE_DIR="deployment-package-$TIMESTAMP"
    mkdir -p "$PACKAGE_DIR"

    # Copy essential files
    print_info "Copying deployment files..."
    cp Dockerfile "$PACKAGE_DIR/"
    cp docker-compose.yml "$PACKAGE_DIR/"
    cp requirements.txt "$PACKAGE_DIR/"
    cp alembic.ini "$PACKAGE_DIR/"
    cp -r alembic "$PACKAGE_DIR/"
    cp -r src "$PACKAGE_DIR/"
    cp -r frontend "$PACKAGE_DIR/"

    # Copy env example
    if [[ -f ".env.example" ]]; then
        cp .env.example "$PACKAGE_DIR/"
    fi

    # Backup and include database
    print_info "Backing up database..."
    backup_database
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.db 2>/dev/null | head -1)
    if [[ -n "$LATEST_BACKUP" ]]; then
        mkdir -p "$PACKAGE_DIR/data"
        cp "$LATEST_BACKUP" "$PACKAGE_DIR/data/whoisonfirst.db"
        print_success "Database included in package"
    fi

    # Include .env if user confirms
    if [[ -f ".env" ]]; then
        echo ""
        read -p "Include .env file with credentials? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env "$PACKAGE_DIR/"
            print_success "Environment file included"
            print_warning "SECURITY: Package contains credentials - transfer securely!"
        else
            print_info "Skipped .env - recipient will need to create their own"
        fi
    fi

    # Create simple README
    cat > "$PACKAGE_DIR/DEPLOY.md" << 'DEPLOY_EOF'
# WhoIsOnFirst Deployment

## Quick Start

1. **Extract and navigate:**
   ```bash
   cd deployment-package-*/
   ```

2. **Configure environment:**
   ```bash
   # If .env not included, copy and edit:
   cp .env.example .env
   # Edit with your Twilio credentials
   ```

3. **Build and start:**
   ```bash
   # Using Docker:
   docker-compose up -d

   # Using Podman:
   podman-compose up -d
   ```

4. **Verify:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy",...}
   ```

5. **Access:**
   - Web UI: http://localhost:8000/
   - API Docs: http://localhost:8000/docs
   - Default login: admin / admin (CHANGE IMMEDIATELY!)

## Database

The `data/whoisonfirst.db` file contains the pre-configured:
- Team members and rotation order
- Shift schedule templates
- Existing schedule assignments
- Application settings

## Container Runtime

This image uses Red Hat UBI9 with Python 3.12, compatible with:
- Docker
- Podman
- Kubernetes (any orchestrator)
- OpenShift

## Ports

- 8000: HTTP (web UI + API)

## Volumes

- `/app/data`: SQLite database (persistent)
DEPLOY_EOF

    print_success "Deployment README created"

    # Create archive
    ARCHIVE_NAME="whoisonfirst-deployment-$TIMESTAMP.tar.gz"
    tar -czf "$ARCHIVE_NAME" "$PACKAGE_DIR"
    rm -rf "$PACKAGE_DIR"

    echo ""
    print_success "Deployment package created: $ARCHIVE_NAME"
    ls -lh "$ARCHIVE_NAME"
    echo ""
    print_info "Transfer this file to your server and extract with:"
    echo "  tar -xzf $ARCHIVE_NAME"
}

# Main
case "${1:-}" in
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    package)
        create_deployment_package
        ;;
    *)
        echo "WhoIsOnFirst Database Backup & Restore"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  backup   - Backup database and .env to ./backups/"
        echo "  restore  - Restore database from backup file"
        echo "  package  - Create complete deployment package (tar.gz)"
        echo ""
        echo "Examples:"
        echo "  $0 backup"
        echo "  $0 restore ./backups/whoisonfirst-20260204-150000.db"
        echo "  $0 package"
        echo ""
        echo "Environment variables:"
        echo "  CONTAINER_NAME  - Container name (default: whoisonfirst-dev)"
        echo "  BACKUP_DIR      - Backup directory (default: ./backups)"
        ;;
esac
