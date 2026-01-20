#!/usr/bin/env python3
"""
Migration script to import recipes.json into MongoDB
Usage: python migrate_to_mongo.py
"""

import json
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

def parse_ingredient(ingredient_str):
    """
    Parse ingredient string into structured format.
    This is a simple parser - can be enhanced later.
    """
    return {
        "original": ingredient_str,
        "item": ingredient_str.lower().strip(),
        # TODO: Add parsing for quantity, unit, preparation
    }

def migrate_recipes():
    """Migrate recipes from JSON to MongoDB"""
    
    # Get MongoDB credentials from environment
    mongo_password = os.getenv('MONGO_PASSWORD', 'changeme123')
    mongo_database = os.getenv('MONGODB_DATABASE', 'dinner_menu')
    
    # Build connection string for localhost (not Docker internal network)
    # URL encode the password to handle special characters
    encoded_password = quote_plus(mongo_password)
    mongodb_uri = f'mongodb://admin:{encoded_password}@localhost:27017/'
    
    print(f"Connecting to MongoDB at localhost:27017")
    
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        db = client[mongo_database]
        recipes_collection = db['recipes']
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure MongoDB is running: docker ps | grep mongodb")
        print("  2. Check MongoDB logs: docker logs dinner-menu-mongodb")
        print("  3. Verify MongoDB is accessible: docker exec dinner-menu-mongodb mongosh --eval 'db.runCommand(\"ping\")'")
        return
    
    print(f"Connected to MongoDB: {mongodb_uri}")
    print(f"Database: {db.name}")
    
    # Load existing recipes.json
    if not os.path.exists('recipes.json'):
        print("Error: recipes.json not found")
        return
    
    with open('recipes.json', 'r') as f:
        recipes = json.load(f)
    
    print(f"Found {len(recipes)} recipes to migrate")
    
    # Clear existing data (optional - comment out if you want to keep existing)
    # recipes_collection.delete_many({})
    
    migrated_count = 0
    skipped_count = 0
    
    for recipe in recipes:
        # Check if recipe already exists by title
        existing = recipes_collection.find_one({"title": recipe["title"]})
        if existing:
            print(f"Skipping '{recipe['title']}' - already exists")
            skipped_count += 1
            continue
        
        # Transform recipe data
        mongo_recipe = {
            "title": recipe["title"],
            "date": datetime.strptime(recipe["date"], "%Y-%m-%d") if recipe.get("date") else None,
            "ingredients": [parse_ingredient(ing) for ing in recipe.get("ingredients", [])],
            "oven": recipe.get("oven", False),
            "stove": recipe.get("stove", False),
            "portions": int(recipe.get("portions", 1)) if recipe.get("portions") else 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            # Additional fields for future use
            "tags": [],
            "difficulty": None,
            "cook_time": None,
            "prep_time": None,
        }
        
        # Insert into MongoDB
        result = recipes_collection.insert_one(mongo_recipe)
        print(f"✓ Migrated: {recipe['title']} (ID: {result.inserted_id})")
        migrated_count += 1
    
    print(f"\nMigration complete!")
    print(f"  Migrated: {migrated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total in DB: {recipes_collection.count_documents({})}")
    
    # Create indexes for better performance
    print("\nCreating indexes...")
    recipes_collection.create_index("title")
    recipes_collection.create_index("oven")
    recipes_collection.create_index("stove")
    recipes_collection.create_index("portions")
    recipes_collection.create_index("ingredients.item")
    recipes_collection.create_index("tags")
    print("✓ Indexes created")
    
    client.close()

if __name__ == "__main__":
    migrate_recipes()
