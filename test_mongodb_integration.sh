#!/bin/bash
# Test MongoDB integration locally

echo "🧪 Testing MongoDB Integration"
echo "=============================="

# Check MongoDB is running
if ! docker ps | grep -q dinner-menu-mongodb; then
    echo "❌ MongoDB is not running. Start it with: docker compose up -d mongodb"
    exit 1
fi

echo "✅ MongoDB is running"
echo ""

# Test connection
echo "Testing MongoDB connection..."
python3 << 'EOF'
try:
    from db import RecipeDB
    db = RecipeDB()
    count = db.collection.count_documents({})
    print(f"✅ Connected to MongoDB - {count} recipes found")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)
EOF

echo ""
echo "Testing API endpoints..."
echo ""

# Start API in background
echo "Starting API server..."
python app.py > /tmp/api.log 2>&1 &
API_PID=$!
sleep 3

# Test health endpoint
echo "1. Testing /api/health..."
HEALTH=$(curl -s http://localhost:5000/api/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
fi

# Test recipes endpoint
echo "2. Testing /api/recipes..."
RECIPES=$(curl -s http://localhost:5000/api/recipes)
if echo "$RECIPES" | grep -q "success"; then
    COUNT=$(echo "$RECIPES" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
    echo "   ✅ Recipes endpoint returned $COUNT recipes"
else
    echo "   ❌ Recipes endpoint failed"
fi

# Test dinner menu endpoint
echo "3. Testing /api/dinner-menu..."
MENU=$(curl -s "http://localhost:5000/api/dinner-menu?days=5")
if echo "$MENU" | grep -q "grocery_list"; then
    echo "   ✅ Dinner menu endpoint working"
else
    echo "   ❌ Dinner menu endpoint failed"
fi

# Cleanup
kill $API_PID 2>/dev/null

echo ""
echo "=============================="
echo "✅ MongoDB Integration Tests Complete"
echo "=============================="
echo ""
echo "Your app is now using MongoDB!"
echo "Next: docker compose up -d to run with MongoDB"
