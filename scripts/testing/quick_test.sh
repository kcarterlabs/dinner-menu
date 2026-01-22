#!/bin/bash
echo "===== QUICK SYSTEM TEST ====="
echo

echo "1. Containers:"
docker ps --filter "name=dinner-menu" --format "  {{.Names}}: {{.Status}}"
echo

echo "2. MongoDB Connection:"
python3 -c "from db import RecipeDB; db = RecipeDB(); r = db.get_all_recipes(); print(f'  ✓ {len(r)} recipes')" && echo "  ✓ Connected" || echo "  ✗ Failed"
echo

echo "3. API Health:"
curl -s -m 5 http://localhost:5000/api/health && echo " ✓" || echo "  ✗ Failed"
echo

echo "4. Frontend:"
curl -s -m 5 http://localhost:5173/ > /dev/null && echo "  ✓ Accessible" || echo "  ✗ Failed"
echo

echo "5. Dinner Menu Generation:"
curl -s -m 10 -X POST http://localhost:5000/api/dinner-menu -H "Content-Type: application/json" -d '{"num_dinners":2}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  ✓ {len(d[\"menu\"])} recipes, {len(d[\"grocery_list\"])} grocery items')" && echo || echo "  ✗ Failed"

echo
echo "===== TEST COMPLETE ====="
