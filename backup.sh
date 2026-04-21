#!/bin/bash

set -Eeuo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$SCRIPT_DIR}"
BACKUP_ROOT="${BACKUP_ROOT:-$PROJECT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_NAME="${BACKUP_NAME:-rag-backup-$TIMESTAMP}"
WORK_DIR="$BACKUP_ROOT/$BACKUP_NAME"
ARCHIVE_PATH="$BACKUP_ROOT/$BACKUP_NAME.tar.gz"

REMOTE_HOST="${REMOTE_HOST:-16.52.128.161}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_BASE_DIR="${REMOTE_BASE_DIR:-/opt/rag-transfer}"
REMOTE_DIR="$REMOTE_BASE_DIR/$BACKUP_NAME"

INCLUDE_REDIS="${INCLUDE_REDIS:-0}"
STOP_APP_SERVICES="${STOP_APP_SERVICES:-1}"
RESTART_APP_SERVICES="${RESTART_APP_SERVICES:-1}"
TRANSFER_BACKUP="${TRANSFER_BACKUP:-1}"

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

archive_volume() {
    local volume_name="$1"
    local output_name="$2"

    docker run --rm \
        -v "$volume_name:/from:ro" \
        -v "$WORK_DIR:/to" \
        alpine:3.20 \
        sh -c "cd /from && tar czf \"/to/$output_name\" ."
}

restart_app_services() {
    if [ "$STOP_APP_SERVICES" = "1" ] && [ "$RESTART_APP_SERVICES" = "1" ]; then
        info "Restarting api and worker services..."
        docker compose up -d api worker >/dev/null
        success "api and worker restarted"
    fi
}

trap restart_app_services EXIT

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Starting Backup${NC}"
echo -e "${GREEN}========================================${NC}"

cd "$PROJECT_DIR"

[ -f "docker-compose.yml" ] || fail "docker-compose.yml not found in $PROJECT_DIR"
[ -f ".env" ] || fail ".env not found in $PROJECT_DIR"

require_command docker
require_command tar
require_command gzip

if [ "$TRANSFER_BACKUP" = "1" ]; then
    require_command ssh
    require_command scp
fi

mkdir -p "$WORK_DIR"

info "[1/7] Making sure required data services are available..."
docker compose up -d postgres chroma redis >/dev/null
success "postgres, chroma and redis are available"

if [ "$STOP_APP_SERVICES" = "1" ]; then
    info "[2/7] Stopping api and worker for a consistent backup..."
    docker compose stop api worker >/dev/null || true
    success "api and worker stopped"
else
    info "[2/7] Skipping api/worker stop because STOP_APP_SERVICES=$STOP_APP_SERVICES"
fi

info "[3/7] Dumping PostgreSQL..."
docker compose exec -T postgres pg_dump -U rag rag | gzip > "$WORK_DIR/postgres.sql.gz"
success "PostgreSQL dump created"

info "[4/7] Archiving project files..."
tar czf "$WORK_DIR/project-files.tar.gz" \
    --exclude='./backups' \
    --exclude='./.git/index.lock' \
    .
success "Project files archived"

info "[5/7] Archiving Chroma volume..."
docker compose stop chroma >/dev/null
CHROMA_VOLUME="$(get_named_volume_for_service chroma /chroma/chroma)"
archive_volume "$CHROMA_VOLUME" "chromadata.tar.gz"
docker compose start chroma >/dev/null
success "Chroma volume archived"

if [ "$INCLUDE_REDIS" = "1" ]; then
    info "[6/7] Archiving Redis volume..."
    docker compose stop redis >/dev/null
    REDIS_VOLUME="$(get_named_volume_for_service redis /data)"
    archive_volume "$REDIS_VOLUME" "redisdata.tar.gz"
    docker compose start redis >/dev/null
    success "Redis volume archived"
else
    info "[6/7] Skipping Redis volume (set INCLUDE_REDIS=1 if you need queued jobs)"
fi

cat > "$WORK_DIR/manifest.env" <<EOF
BACKUP_NAME=$BACKUP_NAME
CREATED_AT=$(date -Iseconds)
SOURCE_HOST=$(hostname)
PROJECT_DIR=$PROJECT_DIR
INCLUDE_REDIS=$INCLUDE_REDIS
REMOTE_HOST=$REMOTE_HOST
REMOTE_USER=$REMOTE_USER
REMOTE_DIR=$REMOTE_DIR
EOF

info "[7/7] Packaging backup bundle..."
tar czf "$ARCHIVE_PATH" -C "$BACKUP_ROOT" "$BACKUP_NAME"
success "Backup bundle created: $ARCHIVE_PATH"

if [ "$TRANSFER_BACKUP" = "1" ]; then
    info "Creating remote directory on ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR} ..."
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '$REMOTE_DIR'"

    info "Transferring backup bundle and restore script..."
    scp "$ARCHIVE_PATH" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    scp "$PROJECT_DIR/restore.sh" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "chmod +x '$REMOTE_DIR/restore.sh'"
    success "Backup transferred to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
fi

echo
success "Backup completed successfully"
echo "Local bundle: $ARCHIVE_PATH"
if [ "$TRANSFER_BACKUP" = "1" ]; then
    echo "Remote files:"
    echo "  $REMOTE_DIR/$(basename "$ARCHIVE_PATH")"
    echo "  $REMOTE_DIR/restore.sh"
fi
