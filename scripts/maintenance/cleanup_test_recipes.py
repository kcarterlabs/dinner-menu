#!/usr/bin/env python3
"""
Cleanup script to remove test recipes from MongoDB
"""

import sys
import os

# Add parent directory to Python path to import db module
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Ensure we connect to localhost when running from host
if 'MONGODB_URI' not in os.environ:
    os.environ['MONGODB_URI'] = f"mongodb://admin:{os.getenv('MONGO_PASSWORD', 'changeme123')}@localhost:27017/"

from db import RecipeDB

def cleanup_test_recipes():
    """Remove all recipes with 'test' in the title"""
    try:
        db = RecipeDB()
    except Exception as e:
        print(f"✗ Could not connect to MongoDB: {e}")
        print("Make sure MongoDB is running (docker ps | grep mongodb)")
        return 0
    
    # Find all test recipes (case-insensitive)
    test_recipes = list(db.collection.find({'title': {'$regex': 'test', '$options': 'i'}}))
    
    if not test_recipes:
        print("✓ No test recipes found")
        return 0
    
    print(f"Found {len(test_recipes)} test recipes:")
    for recipe in test_recipes:
        print(f"  - {recipe['title']}")
    
    print()
    # Auto-confirm if run with --yes flag
    if len(sys.argv) > 1 and sys.argv[1] == '--yes':
        confirm = 'yes'
        print("Auto-confirming deletion (--yes flag)")
    else:
        confirm = input("Delete these recipes? (yes/no): ")
    
    if confirm.lower() not in ['yes', 'y']:
        print("Cancelled")
        return 0
    
    deleted_count = 0
    for recipe in test_recipes:
        recipe_id = str(recipe['_id'])
        if db.delete_recipe(recipe_id):
            print(f"  ✓ Deleted: {recipe['title']}")
            deleted_count += 1
        else:
            print(f"  ✗ Failed to delete: {recipe['title']}")
    
    print(f"\n✓ Deleted {deleted_count} test recipes")
    print(f"Remaining recipes: {db.collection.count_documents({})}")
    
    return deleted_count

if __name__ == "__main__":
    try:
        cleanup_test_recipes()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
