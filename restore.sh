#!/bin/bash

set -Eeuo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSFER_DIR="${TRANSFER_DIR:-$SCRIPT_DIR}"
BACKUP_ARCHIVE="${BACKUP_ARCHIVE:-$(ls -1t "$TRANSFER_DIR"/rag-backup-*.tar.gz 2>/dev/null | head -n 1 || true)}"
TARGET_PROJECT_DIR="${TARGET_PROJECT_DIR:-/opt/rag-wordpress}"
WORK_ROOT="${WORK_ROOT:-$TRANSFER_DIR/restore-work}"

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo -e "${RED}Error: required command not found: $1${NC}"
        exit 1
    fi
}

info() {
    echo -e "${YELLOW}$1${NC}"
}

success() {
    echo -e "${GREEN}$1${NC}"
}

fail() {
    echo -e "${RED}$1${NC}"
    exit 1
}

get_named_volume_for_service() {
    local service="$1"
    local destination="$2"
    local container_id
    local volume_name

    container_id="$(docker compose ps -aq "$service")"
    if [ -z "$container_id" ]; then
        fail "Service '$service' does not have a Compose container yet. Start it first with: docker compose up -d $service"
    fi

    volume_name="$(docker inspect "$container_id" \
        --format "{{range .Mounts}}{{if and (eq .Destination \"$destination\") (eq .Type \"volume\")}}{{.Name}}{{end}}{{end}}")"

    if [ -z "$volume_name" ]; then
        fail "Could not find Docker volume for service '$service' at '$destination'"
    fi

    printf '%s\n' "$volume_name"
}

restore_volume() {
    local archive_path="$1"
    local volume_name="$2"

    docker run --rm \
        -v "$volume_name:/to" \
        -v "$WORK_DIR:/from:ro" \
        alpine:3.20 \
        sh -c "rm -rf /to/* /to/.[!.]* /to/..?* 2>/dev/null || true; cd /to && tar xzf \"/from/$archive_path\""
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Starting Restore${NC}"
echo -e "${GREEN}========================================${NC}"

[ -n "$BACKUP_ARCHIVE" ] || fail "No backup archive found in $TRANSFER_DIR"
[ -f "$BACKUP_ARCHIVE" ] || fail "Backup archive not found: $BACKUP_ARCHIVE"

require_command docker
require_command tar
require_command gzip

BACKUP_BASENAME="$(basename "$BACKUP_ARCHIVE" .tar.gz)"
WORK_DIR="$WORK_ROOT/$BACKUP_BASENAME"

info "[1/7] Unpacking backup bundle..."
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR" "$TARGET_PROJECT_DIR"
tar xzf "$BACKUP_ARCHIVE" -C "$WORK_ROOT"
success "Backup bundle unpacked"

RESTORE_PAYLOAD_DIR="$WORK_DIR"
[ -f "$RESTORE_PAYLOAD_DIR/project-files.tar.gz" ] || fail "project-files.tar.gz not found inside backup bundle"
[ -f "$RESTORE_PAYLOAD_DIR/postgres.sql.gz" ] || fail "postgres.sql.gz not found inside backup bundle"

info "[2/7] Restoring project files to $TARGET_PROJECT_DIR ..."
tar xzf "$RESTORE_PAYLOAD_DIR/project-files.tar.gz" -C "$TARGET_PROJECT_DIR"
success "Project files restored"

cd "$TARGET_PROJECT_DIR"
[ -f "docker-compose.yml" ] || fail "docker-compose.yml not found after restore"
[ -f ".env" ] || fail ".env not found after restore"

info "[3/7] Starting data services to create containers and volumes..."
docker compose up -d postgres chroma redis >/dev/null
success "Data services started"

info "[4/7] Restoring Chroma volume..."
docker compose stop chroma >/dev/null
CHROMA_VOLUME="$(get_named_volume_for_service chroma /chroma/chroma)"
restore_volume "chromadata.tar.gz" "$CHROMA_VOLUME"
docker compose start chroma >/dev/null
success "Chroma volume restored"

if [ -f "$RESTORE_PAYLOAD_DIR/redisdata.tar.gz" ]; then
    info "[5/7] Restoring Redis volume..."
    docker compose stop redis >/dev/null
    REDIS_VOLUME="$(get_named_volume_for_service redis /data)"
    restore_volume "redisdata.tar.gz" "$REDIS_VOLUME"
    docker compose start redis >/dev/null
    success "Redis volume restored"
else
    info "[5/7] Redis backup not present, skipping Redis restore"
fi

info "[6/7] Recreating and restoring PostgreSQL database..."
docker compose exec -T postgres psql -U rag -d postgres -c "DROP DATABASE IF EXISTS rag;"
docker compose exec -T postgres psql -U rag -d postgres -c "CREATE DATABASE rag;"
gunzip -c "$RESTORE_PAYLOAD_DIR/postgres.sql.gz" | docker compose exec -T postgres psql -U rag -d rag
success "PostgreSQL restored"

info "[7/7] Starting application services..."
docker compose up -d api worker >/dev/null
success "api and worker started"

echo
success "Restore completed successfully"
echo "Project directory: $TARGET_PROJECT_DIR"
echo "Backup archive: $BACKUP_ARCHIVE"
echo
echo "Useful checks:"
echo "  cd $TARGET_PROJECT_DIR && docker compose ps"
echo "  curl http://localhost:8001/health"
