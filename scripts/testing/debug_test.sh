#!/bin/bash
# Debug MongoDB integration tests

echo "=== MongoDB Test Debug ==="
echo

# Check if MongoDB is running
echo "1. MongoDB Container Status:"
docker ps --filter "name=dinner-menu-mongodb" --format "table {{.Names}}\t{{.Status}}"
echo

# Check environment variables
echo "2. Environment Variables:"
if [ -f .env ]; then
    echo "   .env file exists: YES"
    echo "   MONGO_PASSWORD length: $(grep MONGO_PASSWORD .env | cut -d'=' -f2 | wc -c) chars"
else
    echo "   .env file exists: NO"
fi
echo

# Test MongoDB connection from Python
echo "3. Python MongoDB Connection Test:"
python3 << 'EOF'
import os
import sys

# Load .env
from dotenv import load_dotenv
load_dotenv()

print(f"   MONGO_PASSWORD set: {'Yes' if os.getenv('MONGO_PASSWORD') else 'No'}")

try:
    from db import MongoDB
    mongo = MongoDB()
    print(f"   ✓ Connected to: {mongo.db.name}")
    print(f"   ✓ Recipe count: {mongo.db.recipes.count_documents({})}")
    mongo.close()
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    sys.exit(1)
EOF

echo
echo "4. Running single MongoDB test:"
python3 -m pytest tests/test_mongodb_integration.py::TestMongoDBConnection::test_mongodb_connection -v 2>&1

echo
echo "=== Debug Complete ==="
