#!/usr/bin/env python3
"""Quick test to check MongoDB connection"""

import os
import sys

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Ensure MONGO_PASSWORD is set
if 'MONGO_PASSWORD' not in os.environ:
    print("Loading .env file...")
    from dotenv import load_dotenv
    load_dotenv()

print(f"MONGO_PASSWORD set: {'Yes' if os.getenv('MONGO_PASSWORD') else 'No'}")
print(f"MONGODB_URI: {os.getenv('MONGODB_URI', 'Not set')}")

try:
    from db import MongoDB
    print("\nAttempting MongoDB connection...")
    mongo = MongoDB()
    print(f"✓ Connected successfully!")
    print(f"  Database: {mongo.db.name}")
    print(f"  Collections: {mongo.db.list_collection_names()}")
    
    # Count recipes
    recipes_count = mongo.db.recipes.count_documents({})
    print(f"  Recipe count: {recipes_count}")
    
    mongo.close()
    print("\n✓ MongoDB connection test passed!")
except Exception as e:
    print(f"\n✗ MongoDB connection failed!")
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
