#!/usr/bin/env python3
"""Simplified test runner with clear output"""

import subprocess
import sys

def run_test(name, command):
    """Run a test and return pass/fail"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd='/home/kenny/dinner-menu'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

print("=" * 70)
print("DINNER MENU - TEST RESULTS")
print("=" * 70)
print()

tests = [
    ("MongoDB Connection", 
     "python3 -c 'from db import RecipeDB; db = RecipeDB(); r = db.get_all_recipes(); assert len(r) > 0'"),
    
    ("Structured Ingredients",
     "python3 -c 'from db import RecipeDB; db = RecipeDB(); r = db.get_all_recipes()[0]; ing = r[\"ingredients\"][0]; assert \"quantity\" in ing and \"unit\" in ing and \"item\" in ing'"),
    
    ("Ingredient Aggregation",
     "python3 -c 'from db import RecipeDB; db = RecipeDB(); r = db.get_all_recipes(); ids = [str(x[\"_id\"]) for x in r[:3]]; g = db.aggregate_ingredients(ids); assert len(g) > 0'"),
    
    ("Filter Non-Ingredients",
     "python3 -c 'from db import RecipeDB; db = RecipeDB(); r = db.get_all_recipes(); ids = [str(x[\"_id\"]) for x in r]; g = db.aggregate_ingredients(ids); items = [x[\"item\"] for x in g]; assert not any(\"look it up\" in i.lower() for i in items)'"),
    
    ("Ingredient Parser",
     "python3 -c 'from ingredient_parser import parse_ingredient; r = parse_ingredient(\"1 yellow onion\"); assert r[\"quantity\"] == \"1\" and r[\"item\"] == \"yellow onion\"'"),
    
    ("Fraction Conversion",
     "python3 -c 'from ingredient_parser import quantity_to_float; assert quantity_to_float(\"1/2\") == 0.5 and quantity_to_float(\"1 1/2\") == 1.5'"),
    
    ("API Health",
     "curl -s -f -m 5 http://localhost:5000/api/health"),
    
    ("API Recipes",
     "curl -s -f -m 5 http://localhost:5000/api/recipes"),
    
    ("API Dinner Menu",
     "curl -s -f -m 10 -X POST http://localhost:5000/api/dinner-menu -H 'Content-Type: application/json' -d '{\"num_dinners\":2}'"),
    
    ("Frontend",
     "curl -s -f -m 5 http://localhost:5173/"),
]

passed = 0
failed = 0

for name, command in tests:
    success, stdout, stderr = run_test(name, command)
    if success:
        print(f"✓ {name}")
        passed += 1
    else:
        print(f"✗ {name}")
        if stderr and "Timeout" not in stderr:
            print(f"  Error: {stderr[:200]}")
        failed += 1

print()
print("=" * 70)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 70)

sys.exit(0 if failed == 0 else 1)
