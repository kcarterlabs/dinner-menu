"""
Ingredient parser utility to extract quantity, unit, and item from ingredient strings.
Handles common formats like: '2 cups flour', '1 yellow onion', '1/2 tsp salt', '3-4 cloves garlic'
"""

import re
from fractions import Fraction


def parse_ingredient(ingredient_str):
    """
    Parse an ingredient string into structured components.
    
    Args:
        ingredient_str: String like "2 cups flour" or "1 yellow onion"
    
    Returns:
        dict: {
            "quantity": str,  # e.g., "2", "1/2", "1.5", "3-4", ""
            "unit": str,      # e.g., "cup", "tsp", "lb", ""
            "item": str,      # e.g., "flour", "yellow onion"
            "original": str   # original string for reference
        }
    """
    if not ingredient_str or not isinstance(ingredient_str, str):
        return {
            "quantity": "",
            "unit": "",
            "item": ingredient_str or "",
            "original": ingredient_str or ""
        }
    
    original = ingredient_str.strip()
    text = original.lower().strip()
    
    # Remove periods from common abbreviations (lb., oz., etc.)
    # This normalizes "1 lb." to "1 lb" for consistent parsing
    text = re.sub(r'\b(lb|oz|tsp|tbsp|qt|pt|gal|pkg|fl|dr|c|g|kg|ml|l)\.', r'\1', text)
    
    # Common units (both singular and plural forms)
    units = [
        # Volume
        'cup', 'cups', 'c',
        'tablespoon', 'tablespoons', 'tbsp', 'tbs', 'tb',
        'teaspoon', 'teaspoons', 'tsp', 'ts',
        'fluid ounce', 'fluid ounces', 'fl oz', 'fl. oz.',
        'pint', 'pints', 'pt',
        'quart', 'quarts', 'qt',
        'gallon', 'gallons', 'gal',
        'milliliter', 'milliliters', 'ml',
        'liter', 'liters', 'l',
        # Weight
        'pound', 'pounds', 'lb', 'lbs',
        'ounce', 'ounces', 'oz',
        'gram', 'grams', 'g',
        'kilogram', 'kilograms', 'kg',
        # Other
        'clove', 'cloves',
        'head', 'heads',
        'bunch', 'bunches',
        'package', 'packages', 'pkg',
        'can', 'cans',
        'jar', 'jars',
        'bottle', 'bottles',
        'slice', 'slices',
        'piece', 'pieces',
        'whole',
    ]
    
    # Pattern to match quantity at the start
    # Handles: "2", "1/2", "1.5", "3-4", "2 1/2"
    quantity_pattern = r'^(\d+(?:\.\d+)?(?:\s*/\s*\d+)?(?:\s*-\s*\d+)?(?:\s+\d+/\d+)?)'
    
    match = re.match(quantity_pattern, text)
    
    if match:
        quantity = match.group(1).strip()
        remainder = text[match.end():].strip()
        
        # Check if next word is a unit
        unit = ""
        item = remainder
        
        for u in units:
            # Check if remainder starts with this unit
            pattern = r'^' + re.escape(u) + r'\b'
            if re.match(pattern, remainder):
                unit = u
                item = remainder[len(u):].strip()
                break
        
        return {
            "quantity": quantity,
            "unit": unit,
            "item": item if item else remainder,
            "original": original
        }
    else:
        # No quantity found - might be something like "salt to taste" or just "onion"
        # Check if it starts with a unit
        for u in units:
            pattern = r'^' + re.escape(u) + r'\b'
            if re.match(pattern, text):
                return {
                    "quantity": "",
                    "unit": u,
                    "item": text[len(u):].strip(),
                    "original": original
                }
        
        # No quantity or unit found
        return {
            "quantity": "",
            "unit": "",
            "item": original,
            "original": original
        }


def quantity_to_float(quantity_str):
    """
    Convert a quantity string to a float for aggregation.
    Handles fractions, decimals, and ranges.
    
    Args:
        quantity_str: String like "2", "1/2", "1.5", "3-4"
    
    Returns:
        float: Numeric value, or 0.0 if cannot parse
    """
    if not quantity_str or not isinstance(quantity_str, str):
        return 0.0
    
    quantity_str = quantity_str.strip()
    
    # Handle ranges (take the average)
    if '-' in quantity_str:
        parts = quantity_str.split('-')
        if len(parts) == 2:
            try:
                low = quantity_to_float(parts[0].strip())
                high = quantity_to_float(parts[1].strip())
                return (low + high) / 2
            except:
                pass
    
    # Handle mixed fractions like "2 1/2"
    if ' ' in quantity_str:
        parts = quantity_str.split()
        if len(parts) == 2:
            try:
                whole = float(parts[0])
                frac = float(Fraction(parts[1]))
                return whole + frac
            except:
                pass
    
    # Handle fractions
    if '/' in quantity_str:
        try:
            return float(Fraction(quantity_str))
        except:
            return 0.0
    
    # Handle decimals
    try:
        return float(quantity_str)
    except:
        return 0.0


def normalize_unit(unit):
    """
    Normalize unit to a standard form (singular lowercase).
    
    Args:
        unit: String like "cups", "TBSP", "lb."
    
    Returns:
        str: Normalized unit like "cup", "tbsp", "lb"
    """
    if not unit:
        return ""
    
    unit = unit.lower().strip().rstrip('.')
    
    # Map plural to singular
    plurals = {
        'cups': 'cup',
        'tablespoons': 'tbsp',
        'teaspoons': 'tsp',
        'pounds': 'lb',
        'lbs': 'lb',
        'ounces': 'oz',
        'cloves': 'clove',
        'heads': 'head',
        'bunches': 'bunch',
        'packages': 'package',
        'cans': 'can',
        'jars': 'jar',
        'bottles': 'bottle',
        'slices': 'slice',
        'pieces': 'piece',
        'grams': 'gram',
        'kilograms': 'kg',
        'milliliters': 'ml',
        'liters': 'liter',
        'pints': 'pint',
        'quarts': 'quart',
        'gallons': 'gallon',
    }
    
    # Common abbreviations
    abbrevs = {
        'tbs': 'tbsp',
        'tb': 'tbsp',
        'ts': 'tsp',
        'c': 'cup',
        'fl oz': 'fl oz',
        'fl. oz.': 'fl oz',
        'pt': 'pint',
        'qt': 'quart',
        'gal': 'gallon',
        'pkg': 'package',
        'g': 'gram',
        'l': 'liter',
    }
    
    unit = plurals.get(unit, unit)
    unit = abbrevs.get(unit, unit)
    
    return unit


if __name__ == "__main__":
    # Test the parser
    test_cases = [
        "1 yellow onion",
        "1/2 yellow onion",
        "2 cups flour",
        "1/4 tsp salt",
        "3-4 cloves garlic",
        "2 1/2 cups sugar",
        "salt to taste",
        "1 lb ground beef",
        "2 tablespoons olive oil",
        "onion",
        "",
    ]
    
    print("Testing ingredient parser:\n")
    for test in test_cases:
        result = parse_ingredient(test)
        print(f"Input:    '{test}'")
        print(f"Quantity: '{result['quantity']}'")
        print(f"Unit:     '{result['unit']}'")
        print(f"Item:     '{result['item']}'")
        if result['quantity']:
            print(f"Float:    {quantity_to_float(result['quantity'])}")
        print()
