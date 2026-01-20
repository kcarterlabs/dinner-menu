#!/usr/bin/env python3
"""
Migration script to update ingredient structure from:
    {"original": "1 yellow onion"}
to:
    {"quantity": "1", "unit": "", "item": "yellow onion", "original": "1 yellow onion"}
"""

import os
import sys
from dotenv import load_dotenv
from ingredient_parser import parse_ingredient
from db import MongoDB, RecipeDB

load_dotenv()


def migrate_recipe_ingredients(recipe_db):
    """
    Update all recipes to use structured ingredients.
    """
    recipes = recipe_db.get_all_recipes()
    
    print(f"Found {len(recipes)} recipes to migrate\n")
    
    updated_count = 0
    skipped_count = 0
    
    for recipe in recipes:
        recipe_id = str(recipe['_id'])
        title = recipe.get('title', 'Unknown')
        ingredients = recipe.get('ingredients', [])
        
        needs_update = False
        new_ingredients = []
        
        for ing in ingredients:
            # Check if already properly structured (has quantity, unit, item keys)
            if isinstance(ing, dict) and 'quantity' in ing and 'unit' in ing and 'item' in ing:
                # Already fully structured
                new_ingredients.append(ing)
            elif isinstance(ing, dict) and 'original' in ing:
                # Old format: {"original": "1 yellow onion"} or {"original": "...", "item": "..."}
                parsed = parse_ingredient(ing['original'])
                new_ingredients.append(parsed)
                needs_update = True
            elif isinstance(ing, str):
                # Even older format: just a string
                parsed = parse_ingredient(ing)
                new_ingredients.append(parsed)
                needs_update = True
            else:
                # Unknown format, keep as is
                new_ingredients.append(ing)
        
        if needs_update:
            print(f"Updating: {title}")
            print(f"  Before: {ingredients[0] if ingredients else 'N/A'}")
            print(f"  After:  {new_ingredients[0] if new_ingredients else 'N/A'}")
            print()
            
            # Update the recipe
            recipe_db.update_recipe(recipe_id, {'ingredients': new_ingredients})
            updated_count += 1
        else:
            skipped_count += 1
    
    print(f"\n{'='*60}")
    print(f"Migration complete!")
    print(f"  Updated: {updated_count} recipes")
    print(f"  Skipped: {skipped_count} recipes (already migrated)")
    print(f"{'='*60}")


def main():
    print("="*60)
    print("Structured Ingredients Migration")
    print("="*60)
    print()
    
    # Connect to MongoDB
    try:
        recipe_db = RecipeDB()
        print(f"✓ Connected to MongoDB\n")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    # Confirm migration
    response = input("This will update ALL recipes with structured ingredients. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)
    
    print()
    
    # Run migration
    try:
        migrate_recipe_ingredients(recipe_db)
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
