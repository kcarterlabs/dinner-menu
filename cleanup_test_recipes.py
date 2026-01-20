#!/usr/bin/env python3
"""
Cleanup script to remove test recipes from MongoDB
"""

import sys
from db import RecipeDB

def cleanup_test_recipes():
    """Remove all recipes with 'test' in the title"""
    db = RecipeDB()
    
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
