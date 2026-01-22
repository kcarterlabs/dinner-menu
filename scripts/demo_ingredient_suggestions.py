#!/usr/bin/env python3
"""
Interactive demo of the ingredient suggestion feature
Run this to see how the fuzzy matching works
"""

import json
from difflib import SequenceMatcher

def get_all_ingredients():
    """Extract all unique ingredients from recipes.json"""
    try:
        with open('recipes.json', 'r') as f:
            recipes = json.load(f)
        
        ingredients_set = set()
        
        for recipe in recipes:
            for ingredient in recipe.get('ingredients', []):
                ingredient_lower = ingredient.lower().strip()
                ingredients_set.add(ingredient_lower)
        
        return sorted(list(ingredients_set))
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return []

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

def demo():
    """Run interactive demo"""
    print("=" * 70)
    print("INGREDIENT SUGGESTION FEATURE - Interactive Demo")
    print("=" * 70)
    print()
    
    print("Loading ingredients from recipes.json...")
    all_ingredients = get_all_ingredients()
    
    if not all_ingredients:
        print("❌ No ingredients found. Make sure recipes.json exists.")
        return
    
    print(f"✓ Loaded {len(all_ingredients)} unique ingredients")
    print()
    print("Sample ingredients:")
    for i, ing in enumerate(all_ingredients[:10], 1):
        print(f"  {i}. {ing}")
    print()
    
    # Test cases
    print("=" * 70)
    print("FUZZY MATCHING EXAMPLES")
    print("=" * 70)
    print()
    
    test_cases = [
        ("tomato", "Exact substring match"),
        ("pasta", "Multiple variations"),
        ("onio", "Typo - should match 'onion'"),
        ("garli", "Typo - should match 'garlic'"),
        ("chick", "Partial match for 'chicken'"),
        ("oliv", "Should match olive oil variants"),
        ("salt", "Common ingredient"),
        ("xyz123", "No matches expected"),
    ]
    
    for input_text, description in test_cases:
        print(f"🔍 Search: '{input_text}' ({description})")
        similar = find_similar_ingredients(input_text, all_ingredients)
        
        if similar:
            print(f"   💡 Found {len(similar)} match(es):")
            for i, match in enumerate(similar[:5], 1):
                # Calculate similarity for display
                ratio = SequenceMatcher(None, input_text.lower(), match).ratio()
                stars = "★" * int(ratio * 5)
                print(f"      {i}. {match:<50} {stars} ({ratio:.2f})")
        else:
            print(f"   ⚠️  No similar ingredients found")
        print()
    
    # Interactive mode
    print("=" * 70)
    print("INTERACTIVE MODE")
    print("=" * 70)
    print("Type an ingredient to search (or 'quit' to exit)")
    print()
    
    while True:
        try:
            user_input = input("🔍 Search ingredient: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            if len(user_input) < 2:
                print("   Type at least 2 characters to search...")
                continue
            
            similar = find_similar_ingredients(user_input, all_ingredients)
            
            if similar:
                print(f"   💡 Found {len(similar)} match(es):")
                for i, match in enumerate(similar, 1):
                    print(f"      {i}. {match}")
            else:
                print(f"   ⚠️  No similar ingredients found. '{user_input}' would be a new ingredient.")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            break

if __name__ == '__main__':
    demo()
