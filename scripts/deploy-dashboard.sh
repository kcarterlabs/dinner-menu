#!/bin/bash
# Deployment Status and Quick Actions Menu

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Dinner Menu - Deployment Dashboard                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check current status
echo "📊 Current Status"
echo "────────────────────────────────────────────────────────────────"

# Docker status
if docker info > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅${NC} Docker: Running"
else
    echo -e "  ${RED}❌${NC} Docker: Not running"
fi

# Containers
if docker ps --format '{{.Names}}' | grep -q "dinner-menu-api"; then
    API_STATUS=$(docker inspect -f '{{.State.Status}}' dinner-menu-api 2>/dev/null)
    echo -e "  ${GREEN}✅${NC} API Container: $API_STATUS"
else
    echo -e "  ${RED}❌${NC} API Container: Not found"
fi

if docker ps --format '{{.Names}}' | grep -q "dinner-menu-vue"; then
    VUE_STATUS=$(docker inspect -f '{{.State.Status}}' dinner-menu-vue 2>/dev/null)
    echo -e "  ${GREEN}✅${NC} Frontend Container: $VUE_STATUS"
else
    echo -e "  ${RED}❌${NC} Frontend Container: Not found"
fi

if docker ps --format '{{.Names}}' | grep -q "dinner-menu-mongodb"; then
    MONGO_STATUS=$(docker inspect -f '{{.State.Status}}' dinner-menu-mongodb 2>/dev/null)
    echo -e "  ${GREEN}✅${NC} MongoDB Container: $MONGO_STATUS"
else
    echo -e "  ${RED}❌${NC} MongoDB Container: Not found"
fi

# Health checks
echo ""
if curl -sf -m 3 http://localhost:5000/api/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅${NC} API Health: Healthy"
else
    echo -e "  ${RED}❌${NC} API Health: Not responding"
fi

if curl -sf -m 3 http://localhost:5173/ > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅${NC} Frontend: Accessible"
else
    echo -e "  ${RED}❌${NC} Frontend: Not accessible"
fi

# Recent deployments
echo ""
echo "📝 Recent Deployments"
echo "────────────────────────────────────────────────────────────────"
if [ -d "backups/deployments" ]; then
    ls -t backups/deployments/*.info 2>/dev/null | head -3 | while read info_file; do
        DEPLOY_NAME=$(grep "Deployment:" "$info_file" | cut -d: -f2- | xargs)
        DEPLOY_DATE=$(grep "Date:" "$info_file" | cut -d: -f2- | xargs)
        echo "  • $DEPLOY_NAME"
        echo "    $DEPLOY_DATE"
    done
else
    echo "  No deployments yet"
fi

# Logs
echo ""
echo "📄 Recent Logs"
echo "────────────────────────────────────────────────────────────────"
if [ -d "logs" ]; then
    ls -t logs/deploy-*.log 2>/dev/null | head -1 | while read log_file; do
        echo "  Latest: $(basename $log_file)"
        echo "  Size: $(du -h "$log_file" | cut -f1)"
    done
else
    echo "  No logs yet"
fi

# Quick Actions
echo ""
echo "🎯 Quick Actions"
echo "────────────────────────────────────────────────────────────────"
echo "  1. Deploy Now (automated)"
echo "  2. Rollback to Previous"
echo "  3. View Logs"
echo "  4. Container Status"
echo "  5. Resource Usage"
echo "  6. Health Check"
echo "  7. Restart Containers"
echo "  8. Exit"
echo ""

read -p "Select action (1-8): " action

case $action in
    1)
        echo ""
        ./scripts/auto-deploy.sh
        ;;
    2)
        echo ""
        ./scripts/rollback.sh
        ;;
    3)
        echo ""
        LATEST_LOG=$(ls -t logs/deploy-*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            less "$LATEST_LOG"
        else
            echo "No logs found"
        fi
        ;;
    4)
        echo ""
        docker ps --filter "name=dinner-menu"
        echo ""
        read -p "Press enter to continue..."
        ;;
    5)
        echo ""
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" $(docker ps --filter "name=dinner-menu" -q)
        echo ""
        read -p "Press enter to continue..."
        ;;
    6)
        echo ""
        echo "Testing API health..."
        curl -v http://localhost:5000/api/health
        echo ""
        echo ""
        echo "Testing frontend..."
        curl -I http://localhost:5173/
        echo ""
        read -p "Press enter to continue..."
        ;;
    7)
        echo ""
        echo "Restarting containers..."
        docker-compose restart
        echo "Done!"
        sleep 2
        ;;
    8)
        exit 0
        ;;
    *)
        echo "Invalid selection"
        ;;
esac
