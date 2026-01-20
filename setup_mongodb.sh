#!/bin/bash
# Setup MongoDB with Docker and migrate existing recipes

set -e

echo "🗄️  MongoDB Setup with Docker"
echo "=============================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Create data directories for persistent storage
echo ""
echo "📁 Creating data directories..."
mkdir -p data/mongodb data/mongodb-config
echo "✅ Directories created: ./data/mongodb"

# Set MongoDB password
echo ""
read -p "Set MongoDB password (default: changeme123): " mongo_password
mongo_password=${mongo_password:-changeme123}

# Update .env file
echo ""
echo "📝 Updating .env configuration..."
if [ -f .env ]; then
    # Remove old MongoDB entries if they exist
    sed -i '/MONGODB_URI/d' .env 2>/dev/null || true
    sed -i '/MONGODB_DATABASE/d' .env 2>/dev/null || true
    sed -i '/MONGO_PASSWORD/d' .env 2>/dev/null || true
fi

cat >> .env << EOF

# MongoDB Configuration
MONGO_PASSWORD=$mongo_password
MONGODB_URI=mongodb://admin:$mongo_password@mongodb:27017/
MONGODB_DATABASE=dinner_menu
EOF

echo "✅ Configuration saved to .env"

# Start MongoDB with docker compose
echo ""
echo "🐳 Starting MongoDB container..."
docker compose up -d mongodb

echo ""
echo "⏳ Waiting for MongoDB to be ready..."
sleep 5

# Check MongoDB health
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec dinner-menu-mongodb mongosh --eval "db.runCommand('ping')" --quiet > /dev/null 2>&1; then
        echo "✅ MongoDB is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Waiting... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ MongoDB failed to start"
    docker logs dinner-menu-mongodb
    exit 1
fi

# Step 2: Install dependencies
echo ""
echo "Step 2: Installing Python dependencies..."
pip install pymongo python-dotenv

# Step 3: Run migration
echo ""
echo "Step 3: Migrating recipes to MongoDB..."
python migrate_to_mongo.py

# Step 4: Verify
echo ""
echo "Step 4: Verifying migration..."
python -c "
from db import RecipeDB
db = RecipeDB()
count = db.collection.count_documents({})
print(f'✅ Migration complete! {count} recipes in MongoDB')
"

echo ""
echo "=============================="
echo "✅ Setup Complete!"
echo "=============================="
echo ""
echo "📊 Your data is stored in: ./data/mongodb"
echo "🔐 MongoDB credentials: admin / $mongo_password"
echo ""
echo "Useful commands:"
echo "  Start MongoDB:  docker compose up -d mongodb"
echo "  Stop MongoDB:   docker compose stop mongodb"
echo "  View logs:      docker logs dinner-menu-mongodb"
echo "  Access shell:   docker exec -it dinner-menu-mongodb mongosh -u admin -p"
echo "  Backup data:    tar -czf mongodb-backup.tar.gz data/mongodb/"
echo ""
echo "Next steps:"
echo "  1. Test the connection: curl http://localhost:5000/api/migrate/check"
echo "  2. Review app_mongo_example.py for integration examples"
echo "  3. Start using MongoDB in your app!"
