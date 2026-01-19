#!/usr/bin/env python3
"""
Test script for ingredient suggestion feature
"""

import json
from difflib import SequenceMatcher

def get_all_ingredients():
    """Extract all unique ingredients from existing recipes"""
    with open('recipes.json', 'r') as f:
        recipes = json.load(f)
    
    ingredients_set = set()
    
    for recipe in recipes:
        for ingredient in recipe.get('ingredients', []):
            ingredient_lower = ingredient.lower().strip()
            ingredients_set.add(ingredient_lower)
    
    return sorted(list(ingredients_set))

def find_similar_ingredients(input_text, all_ingredients, threshold=0.6):
    """Find ingredients similar to the input text using fuzzy matching"""
    if not input_text or len(input_text) < 2:
        return []
    
    input_lower = input_text.lower().strip()
    matches = []
    
    for ingredient in all_ingredients:
        # Check if input is a substring
        if input_lower in ingredient:
            matches.append((ingredient, 1.0))
            continue
        
        # Use fuzzy matching
        ratio = SequenceMatcher(None, input_lower, ingredient).ratio()
        if ratio >= threshold:
            matches.append((ingredient, ratio))
    
    # Sort by similarity score (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    return [match[0] for match in matches[:10]]  # Return top 10 matches

if __name__ == '__main__':
    print("Loading ingredients from recipes.json...")
    all_ingredients = get_all_ingredients()
    print(f"Found {len(all_ingredients)} unique ingredients\n")
    
    # Test cases
    test_inputs = [
        "tomato",
        "pasta",
        "chicken",
        "onio",  # typo for onion
        "garli",  # typo for garlic
        "olive",
        "beef",
    ]
    
    for test_input in test_inputs:
        similar = find_similar_ingredients(test_input, all_ingredients)
        print(f"Input: '{test_input}'")
        if similar:
            print(f"  Found {len(similar)} matches:")
            for match in similar[:5]:  # Show top 5
                print(f"    - {match}")
        else:
            print("  No matches found")
        print()
