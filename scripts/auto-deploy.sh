#!/bin/bash
# Automated deployment script with health checks and rollback capability
# For local Docker deployments

set -e

# Configuration
DEPLOYMENT_NAME="dinner-menu-$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="backups/deployments"
LOG_FILE="logs/deploy-${DEPLOYMENT_NAME}.log"
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=5
ROLLBACK_ENABLED=true

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create logs directory
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$BACKUP_DIR"

# Log function
log() {
    echo -e "${2:-$NC}$1${NC}" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
    echo "  $1" | tee -a "$LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
}

# Rollback function
rollback() {
    log_section "🔄 ROLLING BACK DEPLOYMENT"
    log "Reason: $1" "$RED"
    
    if [ -z "$BACKUP_IMAGE_API" ]; then
        log "No backup found, cannot rollback automatically" "$RED"
        exit 1
    fi
    
    log "Restoring previous containers..." "$YELLOW"
    
    cd "$PROJECT_ROOT"
    
    # Tag backup images back to latest
    if [ -n "$BACKUP_IMAGE_API" ]; then
        docker tag "$BACKUP_IMAGE_API" dinner-menu-api:backup-restored
    fi
    if [ -n "$BACKUP_IMAGE_FRONTEND" ]; then
        docker tag "$BACKUP_IMAGE_FRONTEND" dinner-menu-vue:backup-restored
    fi
    
    # Restart with docker-compose using the tagged images
    docker-compose down
    docker-compose up -d
    
    # Wait and verify rollback
    sleep 10
    if verify_health; then
        log "✅ Rollback successful!" "$GREEN"
        log "Previous version restored and running healthy"
        exit 0
    else
        log "❌ Rollback verification failed!" "$RED"
        log "Manual intervention required"
        exit 1
    fi
}

# Health check function
verify_health() {
    local retries=0
    
    log "Verifying deployment health..." "$BLUE"
    
    while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
        # Check if containers are running
        if ! docker ps --format '{{.Names}}' | grep -q "dinner-menu-api"; then
            log "❌ API container not running" "$RED"
            return 1
        fi
        
        if ! docker ps --format '{{.Names}}' | grep -q "dinner-menu-vue"; then
            log "❌ Frontend container not running" "$RED"
            return 1
        fi
        
        # Check API health endpoint
        if curl -sf -m 5 http://localhost:5000/api/health > /dev/null 2>&1; then
            log "✅ API health check passed" "$GREEN"
            
            # Check if API can fetch recipes
            if curl -sf -m 5 http://localhost:5000/api/recipes > /dev/null 2>&1; then
                log "✅ API recipes endpoint working" "$GREEN"
            else
                log "⚠️  API recipes endpoint not responding" "$YELLOW"
            fi
            
            # Check frontend
            if curl -sf -m 5 http://localhost:5173/ > /dev/null 2>&1; then
                log "✅ Frontend accessible" "$GREEN"
                return 0
            else
                log "⚠️  Frontend not yet accessible, retrying..." "$YELLOW"
            fi
        else
            log "⚠️  API not responding, retry $((retries + 1))/$HEALTH_CHECK_RETRIES" "$YELLOW"
        fi
        
        retries=$((retries + 1))
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log "❌ Health checks failed after $HEALTH_CHECK_RETRIES attempts" "$RED"
    return 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log_section "🔍 PRE-DEPLOYMENT CHECKS"
    
    local checks_passed=true
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log "❌ Docker is not running" "$RED"
        checks_passed=false
    else
        log "✅ Docker is running" "$GREEN"
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log "❌ docker-compose is not installed" "$RED"
        checks_passed=false
    else
        log "✅ docker-compose is available" "$GREEN"
    fi
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log "⚠️  No .env file found, using defaults" "$YELLOW"
    else
        log "✅ .env file found" "$GREEN"
    fi
    
    # Run tests
    log "" 
    log "Running test suite..." "$BLUE"
    cd "$PROJECT_ROOT"
    
    if python -m pytest tests/test_app.py tests/test_e2e.py -q --tb=no >> "$LOG_FILE" 2>&1; then
        log "✅ Tests passed" "$GREEN"
    else
        log "❌ Tests failed - see $LOG_FILE for details" "$RED"
        checks_passed=false
    fi
    
    # Check disk space
    local disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log "⚠️  Disk usage is ${disk_usage}% - consider cleaning up" "$YELLOW"
    else
        log "✅ Disk space OK (${disk_usage}% used)" "$GREEN"
    fi
    
    if [ "$checks_passed" = false ]; then
        log "" "$RED"
        log "Pre-deployment checks failed. Aborting deployment." "$RED"
        exit 1
    fi
    
    log "" "$GREEN"
    log "All pre-deployment checks passed!" "$GREEN"
}

# Backup current deployment
backup_current_deployment() {
    log_section "💾 BACKING UP CURRENT DEPLOYMENT"
    
    # Check if containers exist
    if docker ps -a --format '{{.Names}}' | grep -q "dinner-menu-api"; then
        log "Backing up current API image..." "$BLUE"
        BACKUP_IMAGE_API="dinner-menu-api:backup-$(date +%Y%m%d-%H%M%S)"
        docker commit dinner-menu-api "$BACKUP_IMAGE_API" >> "$LOG_FILE" 2>&1
        log "✅ API backup: $BACKUP_IMAGE_API" "$GREEN"
    else
        log "⚠️  No existing API container to backup" "$YELLOW"
        BACKUP_IMAGE_API=""
    fi
    
    if docker ps -a --format '{{.Names}}' | grep -q "dinner-menu-vue"; then
        log "Backing up current frontend image..." "$BLUE"
        BACKUP_IMAGE_FRONTEND="dinner-menu-vue:backup-$(date +%Y%m%d-%H%M%S)"
        docker commit dinner-menu-vue "$BACKUP_IMAGE_FRONTEND" >> "$LOG_FILE" 2>&1
        log "✅ Frontend backup: $BACKUP_IMAGE_FRONTEND" "$GREEN"
    else
        log "⚠️  No existing frontend container to backup" "$YELLOW"
        BACKUP_IMAGE_FRONTEND=""
    fi
    
    # Backup MongoDB data
    if docker ps --format '{{.Names}}' | grep -q "dinner-menu-mongodb"; then
        log "Backing up MongoDB data..." "$BLUE"
        MONGO_BACKUP_FILE="$BACKUP_DIR/mongodb-${DEPLOYMENT_NAME}.archive"
        docker exec dinner-menu-mongodb mongodump \
            --username admin \
            --password "${MONGO_PASSWORD:-changeme123}" \
            --authenticationDatabase admin \
            --archive="$MONGO_BACKUP_FILE" \
            --gzip >> "$LOG_FILE" 2>&1
        log "✅ MongoDB backup: $MONGO_BACKUP_FILE" "$GREEN"
    fi
    
    # Save backup metadata
    cat > "$BACKUP_DIR/${DEPLOYMENT_NAME}.info" <<EOF
Deployment: $DEPLOYMENT_NAME
Date: $(date)
API Image: ${BACKUP_IMAGE_API:-none}
Frontend Image: ${BACKUP_IMAGE_FRONTEND:-none}
MongoDB Backup: ${MONGO_BACKUP_FILE:-none}
EOF
    
    log "✅ Backup completed" "$GREEN"
}

# Deploy new version
deploy_new_version() {
    log_section "🚀 DEPLOYING NEW VERSION"
    
    cd "$PROJECT_ROOT"
    
    # Pull latest code (if in git repo)
    if [ -d .git ]; then
        log "Pulling latest changes from git..." "$BLUE"
        git pull >> "$LOG_FILE" 2>&1 || log "⚠️  Could not pull from git (might be local changes)" "$YELLOW"
    fi
    
    # Stop current containers
    log "Stopping current containers..." "$BLUE"
    docker-compose down >> "$LOG_FILE" 2>&1
    
    # Build new images
    log "Building new images..." "$BLUE"
    docker-compose build --no-cache >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        log "❌ Build failed!" "$RED"
        if [ "$ROLLBACK_ENABLED" = true ]; then
            rollback "Build failure"
        fi
        exit 1
    fi
    
    log "✅ Build completed" "$GREEN"
    
    # Start new containers
    log "Starting new containers..." "$BLUE"
    docker-compose up -d >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        log "❌ Container startup failed!" "$RED"
        if [ "$ROLLBACK_ENABLED" = true ]; then
            rollback "Container startup failure"
        fi
        exit 1
    fi
    
    log "✅ Containers started" "$GREEN"
    
    # Wait for containers to initialize
    log "Waiting for services to initialize..." "$BLUE"
    sleep 15
}

# Post-deployment verification
post_deployment_verification() {
    log_section "✅ POST-DEPLOYMENT VERIFICATION"
    
    if ! verify_health; then
        log "❌ Post-deployment health checks failed!" "$RED"
        if [ "$ROLLBACK_ENABLED" = true ]; then
            rollback "Health check failure"
        fi
        exit 1
    fi
    
    log "✅ All health checks passed!" "$GREEN"
    
    # Display container status
    log ""
    log "Container Status:" "$BLUE"
    docker ps --filter "name=dinner-menu" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | tee -a "$LOG_FILE"
    
    # Display resource usage
    log ""
    log "Resource Usage:" "$BLUE"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker ps --filter "name=dinner-menu" -q) | tee -a "$LOG_FILE"
}

# Cleanup old backups
cleanup_old_backups() {
    log_section "🧹 CLEANUP"
    
    # Keep only last 5 backups
    log "Cleaning up old backups (keeping last 5)..." "$BLUE"
    
    local backup_count=$(ls -1 "$BACKUP_DIR"/*.info 2>/dev/null | wc -l)
    if [ "$backup_count" -gt 5 ]; then
        ls -t "$BACKUP_DIR"/*.info | tail -n +6 | while read info_file; do
            local base=$(basename "$info_file" .info)
            rm -f "$BACKUP_DIR/${base}"* >> "$LOG_FILE" 2>&1
            log "Removed old backup: $base" "$BLUE"
        done
    fi
    
    # Cleanup old Docker images
    log "Cleaning up old Docker images..." "$BLUE"
    docker image prune -f >> "$LOG_FILE" 2>&1
    
    log "✅ Cleanup completed" "$GREEN"
}

# Main deployment flow
main() {
    log_section "🎯 AUTOMATED DEPLOYMENT STARTED"
    log "Deployment ID: $DEPLOYMENT_NAME"
    log "Log file: $LOG_FILE"
    log "Rollback enabled: $ROLLBACK_ENABLED"
    
    # Run pre-deployment checks
    pre_deployment_checks
    
    # Backup current deployment
    backup_current_deployment
    
    # Deploy new version
    deploy_new_version
    
    # Verify deployment
    post_deployment_verification
    
    # Cleanup
    cleanup_old_backups
    
    # Success!
    log_section "🎉 DEPLOYMENT SUCCESSFUL"
    log "Deployment ID: $DEPLOYMENT_NAME" "$GREEN"
    log "Application is running at:" "$GREEN"
    log "  • API: http://localhost:5000" "$GREEN"
    log "  • Frontend: http://localhost:5173" "$GREEN"
    log ""
    log "Backup saved: $BACKUP_IMAGE_API" "$GREEN"
    log "Log file: $LOG_FILE" "$GREEN"
}

# Handle errors
trap 'log "❌ Deployment failed with error on line $LINENO" "$RED"; if [ "$ROLLBACK_ENABLED" = true ]; then rollback "Script error"; fi' ERR

# Run main deployment
main
