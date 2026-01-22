#!/bin/bash
# Manual rollback script for emergencies

set -e

BACKUP_DIR="backups/deployments"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔄 Manual Rollback Tool"
echo "======================="
echo ""

# List available backups
echo "Available backups:"
echo ""

if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/*.info 2>/dev/null)" ]; then
    echo "❌ No backups found in $BACKUP_DIR"
    exit 1
fi

# Display backups
ls -t "$BACKUP_DIR"/*.info | while read info_file; do
    echo "────────────────────────────────────"
    cat "$info_file"
done

echo ""
echo "────────────────────────────────────"
echo ""

# Ask user which backup to restore
echo "Enter the deployment name to rollback to (or 'cancel' to abort):"
read -r deployment_name

if [ "$deployment_name" = "cancel" ]; then
    echo "Rollback cancelled"
    exit 0
fi

INFO_FILE="$BACKUP_DIR/${deployment_name}.info"

if [ ! -f "$INFO_FILE" ]; then
    echo "❌ Backup not found: $deployment_name"
    exit 1
fi

# Read backup info
API_IMAGE=$(grep "API Image:" "$INFO_FILE" | cut -d: -f2- | xargs)
FRONTEND_IMAGE=$(grep "Frontend Image:" "$INFO_FILE" | cut -d: -f2- | xargs)
MONGODB_BACKUP=$(grep "MongoDB Backup:" "$INFO_FILE" | cut -d: -f2- | xargs)

echo ""
echo "Rollback Details:"
echo "  API: $API_IMAGE"
echo "  Frontend: $FRONTEND_IMAGE"
echo "  MongoDB: $MONGODB_BACKUP"
echo ""

# Confirm rollback
echo -e "${YELLOW}⚠️  This will stop the current deployment and restore the backup.${NC}"
echo "Are you sure? (yes/no)"
read -r confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

echo ""
echo "🔄 Starting rollback..."

# Stop current containers
echo "Stopping current containers..."
docker-compose down

# Restore API
if [ "$API_IMAGE" != "none" ] && [ -n "$API_IMAGE" ]; then
    echo "Restoring API: $API_IMAGE"
    docker tag "$API_IMAGE" dinner-menu-api:latest
fi

# Restore Frontend
if [ "$FRONTEND_IMAGE" != "none" ] && [ -n "$FRONTEND_IMAGE" ]; then
    echo "Restoring Frontend: $FRONTEND_IMAGE"
    docker tag "$FRONTEND_IMAGE" dinner-menu-vue:latest
fi

# Restore MongoDB
if [ "$MONGODB_BACKUP" != "none" ] && [ -n "$MONGODB_BACKUP" ] && [ -f "$MONGODB_BACKUP" ]; then
    echo "Restoring MongoDB data..."
    echo "⚠️  Starting MongoDB container temporarily..."
    docker-compose up -d mongodb
    sleep 10
    
    docker exec -i dinner-menu-mongodb mongorestore \
        --username admin \
        --password "${MONGO_PASSWORD:-changeme123}" \
        --authenticationDatabase admin \
        --archive="$MONGODB_BACKUP" \
        --gzip \
        --drop
    
    echo "✅ MongoDB data restored"
fi

# Start containers
echo "Starting containers with restored images..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

# Verify health
echo "Verifying deployment health..."
if curl -sf -m 5 http://localhost:5000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API health check passed${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
fi

if curl -sf -m 5 http://localhost:5173/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend accessible${NC}"
else
    echo -e "${RED}❌ Frontend not accessible${NC}"
fi

echo ""
echo "🎉 Rollback completed!"
echo "Restored to: $deployment_name"
