#!/bin/bash
# Comprehensive status check

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              DINNER MENU - SYSTEM STATUS                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# 1. Containers
echo "1. Docker Containers:"
docker ps --filter "name=dinner-menu" --format "   {{.Names}}: {{.Status}}" 2>/dev/null || echo "   ✗ Docker not running"
echo

# 2. MongoDB Test Recipes
echo "2. Test Recipes in MongoDB:"
docker exec dinner-menu-api python3 -c "
from db import RecipeDB
db = RecipeDB()
test_recipes = list(db.collection.find({'title': {'\$regex': 'test', '\$options': 'i'}}))
total = db.collection.count_documents({})
print(f'   Test recipes: {len(test_recipes)}')
print(f'   Total recipes: {total}')
if test_recipes:
    print('   Test recipe titles:')
    for r in test_recipes[:5]:
        print(f'      - {r[\"title\"]}')
" 2>&1 | grep -v "WARNING"
echo

# 3. API Health
echo "3. API Status:"
if curl -s -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "   ✓ API responding"
    recipe_count=$(curl -s http://localhost:5000/api/recipes 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    echo "   ✓ Serving $recipe_count recipes"
else
    echo "   ✗ API not responding"
fi
echo

# 4. Frontend
echo "4. Frontend:"
if curl -s -f http://localhost:5173/ > /dev/null 2>&1; then
    echo "   ✓ Accessible at http://localhost:5173"
else
    echo "   ✗ Not accessible"
fi
echo

# 5. Structured Ingredients
echo "5. Data Format:"
docker exec dinner-menu-api python3 -c "
from db import RecipeDB
db = RecipeDB()
recipes = db.get_all_recipes()
if recipes:
    r = recipes[0]
    ing = r['ingredients'][0] if r.get('ingredients') else {}
    if isinstance(ing, dict) and 'quantity' in ing and 'unit' in ing and 'item' in ing:
        print('   ✓ Structured ingredients (quantity/unit/item)')
    else:
        print('   ⚠ Old format detected')
else:
    print('   ⚠ No recipes found')
" 2>&1 | grep -v "WARNING"
echo

echo "╚════════════════════════════════════════════════════════════════╝"
echo "System is $(docker ps --filter 'name=dinner-menu' --format '{{.Names}}' | wc -l)/3 containers running"
echo
