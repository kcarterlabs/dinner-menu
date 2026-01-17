#!/bin/bash

echo "🛑 Stopping containers..."
docker compose down

echo "🗑️  Removing images..."
docker rmi dinner-menu-api dinner-menu-frontend 2>/dev/null || true
docker rmi $(docker images -q dinner-menu) 2>/dev/null || true

echo "🧹 Pruning dangling images..."
docker image prune -f

echo "🔨 Building and starting fresh containers..."
docker compose up -d --build

echo "✅ Done! Containers are running fresh."
echo ""
echo "📊 Container status:"
docker compose ps

echo ""
echo "📝 View logs with: docker compose logs -f"
