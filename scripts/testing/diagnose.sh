#!/bin/bash
# Quick diagnostic script

echo "🔍 Diagnostics"
echo "=============="

echo ""
echo "1. Container Status:"
docker ps --filter "name=dinner-menu" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "2. MongoDB Connection (from API container):"
docker exec dinner-menu-api python -c "
import os
print(f'MONGODB_URI: {os.getenv(\"MONGODB_URI\", \"NOT SET\")}')
print(f'MONGO_PASSWORD: {\"***\" if os.getenv(\"MONGO_PASSWORD\") else \"NOT SET\"}')
try:
    from db import RecipeDB
    db = RecipeDB()
    count = db.collection.count_documents({})
    print(f'✅ MongoDB Connected - {count} recipes')
except Exception as e:
    print(f'❌ MongoDB Error: {e}')
" 2>&1

echo ""
echo "3. API Health Check:"
curl -s http://localhost:5000/api/health | python -m json.tool 2>&1 || echo "❌ API not responding"

echo ""
echo "4. API Recipes Endpoint:"
curl -s http://localhost:5000/api/recipes | python -m json.tool 2>&1 | head -20

echo ""
echo "5. API Logs (last 20 lines):"
docker logs dinner-menu-api --tail 20 2>&1

echo ""
echo "=============="
