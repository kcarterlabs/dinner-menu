#!/usr/bin/env python3
"""
Database cleanup script for MongoDB recipes
- Remove duplicate recipes
- Normalize ingredient names
"""

import os
from dotenv import load_dotenv
from db import RecipeDB, convert_objectid_to_str
from difflib import SequenceMatcher
from collections import defaultdict

load_dotenv()

def similar(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_duplicates():
    """Find duplicate recipes by title"""
    db = RecipeDB()
    recipes = db.get_all_recipes()
    
    title_map = defaultdict(list)
    for recipe in recipes:
        title_map[recipe['title'].lower()].append(recipe)
    
    duplicates = {title: recs for title, recs in title_map.items() if len(recs) > 1}
    return duplicates

def find_similar_ingredients(threshold=0.85):
    """Find similar ingredient names that could be normalized"""
    db = RecipeDB()
    
    # Get all unique ingredients
    pipeline = [
        {"$unwind": "$ingredients"},
        {"$group": {
            "_id": "$ingredients.original",
            "count": {"$sum": 1},
            "recipes": {"$addToSet": "$title"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    all_ingredients = list(db.collection.aggregate(pipeline))
    
    # Find similar pairs
    similar_groups = []
    checked = set()
    
    for i, ing1 in enumerate(all_ingredients):
        if ing1['_id'] in checked:
            continue
        
        group = [ing1]
        for ing2 in all_ingredients[i+1:]:
            if ing2['_id'] in checked:
                continue
            
            if similar(ing1['_id'], ing2['_id']) > threshold:
                group.append(ing2)
                checked.add(ing2['_id'])
        
        if len(group) > 1:
            similar_groups.append(group)
            checked.add(ing1['_id'])
    
    return similar_groups

def remove_duplicate_recipe(recipe_id):
    """Remove a recipe by ID"""
    db = RecipeDB()
    return db.delete_recipe(recipe_id)

def normalize_ingredient(old_name, new_name):
    """Update ingredient name across all recipes"""
    db = RecipeDB()
    
    # Find all recipes with this ingredient
    recipes = list(db.collection.find({
        "ingredients.original": old_name
    }))
    
    updated_count = 0
    for recipe in recipes:
        # Update the ingredient name
        for ing in recipe['ingredients']:
            if ing.get('original') == old_name:
                ing['original'] = new_name
        
        # Save the updated recipe
        db.collection.update_one(
            {"_id": recipe['_id']},
            {"$set": {"ingredients": recipe['ingredients']}}
        )
        updated_count += 1
    
    return updated_count

def main():
    print("🧹 MongoDB Recipe Database Cleanup")
    print("=" * 50)
    print()
    
    while True:
        print("\nOptions:")
        print("  1. Find and remove duplicate recipes")
        print("  2. Find and normalize similar ingredients")
        print("  3. View all ingredients")
        print("  4. Manual ingredient rename")
        print("  5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            print("\n🔍 Searching for duplicate recipes...")
            duplicates = find_duplicates()
            
            if not duplicates:
                print("✅ No duplicates found!")
                continue
            
            print(f"\nFound {len(duplicates)} sets of duplicates:\n")
            
            for title, recipes in duplicates.items():
                print(f"📝 '{title.title()}' ({len(recipes)} copies)")
                for i, recipe in enumerate(recipes):
                    recipe_dict = convert_objectid_to_str(recipe)
                    print(f"   [{i+1}] ID: {recipe_dict['_id']}, Date: {recipe.get('date', 'N/A')}, Ingredients: {len(recipe.get('ingredients', []))}")
                
                print("\n  Actions:")
                print("    - Enter number(s) to delete (e.g., '2,3' or '1')")
                print("    - Press Enter to skip")
                
                to_delete = input("  Delete which? ").strip()
                
                if to_delete:
                    indices = [int(x.strip()) for x in to_delete.split(',')]
                    for idx in sorted(indices, reverse=True):
                        if 1 <= idx <= len(recipes):
                            recipe_id = convert_objectid_to_str(recipes[idx-1])['_id']
                            remove_duplicate_recipe(recipe_id)
                            print(f"    ✅ Deleted copy #{idx}")
                print()
        
        elif choice == "2":
            print("\n🔍 Searching for similar ingredients...")
            similar_groups = find_similar_ingredients()
            
            if not similar_groups:
                print("✅ No similar ingredients found!")
                continue
            
            print(f"\nFound {len(similar_groups)} groups of similar ingredients:\n")
            
            for group in similar_groups:
                print("📦 Similar ingredients:")
                for i, ing in enumerate(group):
                    print(f"   [{i+1}] '{ing['_id']}' (used {ing['count']}x in {len(ing['recipes'])} recipes)")
                
                print("\n  Actions:")
                print("    - Enter the number of the preferred name")
                print("    - Or type a new name to use")
                print("    - Press Enter to skip")
                
                choice_input = input("  Normalize to: ").strip()
                
                if choice_input:
                    if choice_input.isdigit():
                        idx = int(choice_input)
                        if 1 <= idx <= len(group):
                            canonical = group[idx-1]['_id']
                        else:
                            print("  ❌ Invalid choice")
                            continue
                    else:
                        canonical = choice_input
                    
                    print(f"\n  Normalizing to: '{canonical}'")
                    total_updated = 0
                    for ing in group:
                        if ing['_id'] != canonical:
                            count = normalize_ingredient(ing['_id'], canonical)
                            total_updated += count
                            print(f"    ✅ Updated '{ing['_id']}' in {count} recipes")
                    
                    print(f"  ✅ Total: {total_updated} recipes updated\n")
        
        elif choice == "3":
            print("\n📋 All ingredients in database:")
            db = RecipeDB()
            ingredients = db.aggregate_ingredients()
            
            print(f"\nTotal unique ingredients: {len(ingredients)}\n")
            for ing in ingredients:
                print(f"  • {ing['ingredient']} ({ing['count']}x)")
            print()
        
        elif choice == "4":
            old_name = input("\nEnter ingredient name to rename: ").strip()
            new_name = input("Enter new name: ").strip()
            
            if old_name and new_name:
                count = normalize_ingredient(old_name, new_name)
                print(f"✅ Updated {count} recipes")
            else:
                print("❌ Both names required")
        
        elif choice == "5":
            print("\n👋 Cleanup complete!")
            break
        
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
