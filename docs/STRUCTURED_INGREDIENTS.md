# Structured Ingredients Format

The Dinner Menu application uses a structured ingredient format that enables powerful features like ingredient aggregation, smart search, and quantity normalization.

## Overview

Instead of storing ingredients as simple strings:
```json
"ingredients": ["1 cup flour", "2 tsp salt"]
```

We now use a structured format with separate fields:
```json
"ingredients": [
  {
    "quantity": "1",
    "unit": "cup",
    "item": "flour",
    "original": "1 cup flour"
  },
  {
    "quantity": "2",
    "unit": "tsp",
    "item": "salt",
    "original": "2 tsp salt"
  }
]
```

## Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `quantity` | string | Numeric amount (supports fractions, ranges) | `"1"`, `"1/2"`, `"1.5"`, `"2-3"` |
| `unit` | string | Unit of measurement | `"cup"`, `"tsp"`, `"lb"`, `"cloves"` |
| `item` | string | The actual ingredient name | `"flour"`, `"yellow onion"`, `"garlic"` |
| `original` | string | Original unmodified text | `"1 cup all-purpose flour"` |

## Benefits

### 1. **Grocery List Aggregation**
Automatically sum quantities across multiple recipes:
```
Recipe 1: "1 cup flour"
Recipe 2: "2 cups flour"
Result: "3 cups flour" in grocery list
```

### 2. **Smart Search**
Search by specific ingredient:
```javascript
// Find all recipes with garlic
db.recipes.find({ "ingredients.item": "garlic" })
```

### 3. **Unit Normalization**
Different formats are recognized as the same:
- `"1 lb"` = `"1 pound"` = `"1 pounds"`
- `"2 tbsp"` = `"2 tablespoons"` = `"2 Tbsp"`

### 4. **Fuzzy Matching in UI**
Frontend suggests similar ingredients as you type:
- Type "tomat" → Suggests "tomato sauce", "diced tomatoes"

### 5. **Future Features**
The structured format enables:
- Recipe scaling (double/halve quantities)
- Ingredient substitutions
- Nutrition calculations
- Smart shopping lists by store section

## Migration

### Automatic Migration
Existing recipes are automatically converted when loaded:

```python
# Old format strings are parsed automatically
"1 cup flour" → {
  "quantity": "1",
  "unit": "cup",
  "item": "flour",
  "original": "1 cup flour"
}
```

### Manual Migration Script
To migrate all recipes in MongoDB:

```bash
python3 migrate_structured_ingredients.py
```

This script will:
1. Find all recipes with old format
2. Parse each ingredient string
3. Update with structured format
4. Preserve original text in `original` field

## API Usage

### Adding a Recipe

**Frontend format (recommended):**
```javascript
POST /api/recipes
{
  "title": "Test Recipe",
  "ingredients": [
    {
      "quantity": "1",
      "unit": "cup",
      "item": "flour",
      "original": "1 cup flour"
    }
  ],
  "oven": true,
  "stove": false,
  "portions": "4",
  "date": "2026-01-19"
}
```

**Legacy format (still supported):**
```javascript
POST /api/recipes
{
  "title": "Test Recipe",
  "ingredients": ["1 cup flour", "2 tsp salt"],
  // ... other fields
}
```
The API will automatically convert strings to structured format.

### Getting Recipes

```javascript
GET /api/recipes
```

Returns recipes with structured ingredients:
```json
{
  "success": true,
  "count": 18,
  "recipes": [
    {
      "_id": "...",
      "title": "Pasta Primavera",
      "ingredients": [
        {
          "quantity": "1",
          "unit": "lb",
          "item": "pasta",
          "original": "1 lb pasta"
        }
      ]
    }
  ]
}
```

### Grocery List Generation

```javascript
GET /api/dinner-menu/quick?days=5
```

Returns aggregated ingredients:
```json
{
  "dinner_plan": {
    "selected_recipes": [...],
    "grocery_list": [
      "3 cups flour",
      "2 lb ground beef",
      "5 cloves garlic"
    ]
  }
}
```

## Ingredient Parser

The `ingredient_parser.py` module handles parsing:

```python
from ingredient_parser import parse_ingredient

result = parse_ingredient("2 1/2 cups all-purpose flour")
# Returns:
# {
#   "quantity": "2 1/2",
#   "unit": "cups",
#   "item": "all-purpose flour",
#   "original": "2 1/2 cups all-purpose flour"
# }
```

### Supported Formats

**Quantities:**
- Whole numbers: `1`, `2`, `10`
- Fractions: `1/2`, `3/4`, `1/3`
- Mixed numbers: `2 1/2`, `1 1/4`
- Decimals: `1.5`, `2.75`
- Ranges: `2-3`, `4-5`

**Units:**
- Volume: `cup`, `tablespoon` / `tbsp`, `teaspoon` / `tsp`, `quart`, `gallon`, `liter`, `ml`
- Weight: `pound` / `lb`, `ounce` / `oz`, `gram` / `g`, `kilogram` / `kg`
- Count: `clove`, `head`, `bunch`, `piece`, `slice`
- Container: `can`, `jar`, `bottle`, `package`

**Examples:**
```python
parse_ingredient("1 yellow onion")
# { quantity: "1", unit: "", item: "yellow onion", ... }

parse_ingredient("1/2 tsp salt")
# { quantity: "1/2", unit: "tsp", item: "salt", ... }

parse_ingredient("2-3 cloves garlic, minced")
# { quantity: "2-3", unit: "cloves", item: "garlic, minced", ... }

parse_ingredient("salt to taste")
# { quantity: "", unit: "", item: "salt to taste", ... }
```

## Database Schema

MongoDB collection: `recipes`

```javascript
{
  _id: ObjectId("..."),
  title: String,
  date: Date,
  ingredients: [{
    quantity: String,
    unit: String,
    item: String,
    original: String
  }],
  oven: Boolean,
  stove: Boolean,
  portions: Number,
  created_at: Date,
  updated_at: Date,
  tags: [String],  // Optional
  difficulty: String,  // Optional
  cook_time: Number,  // Optional minutes
  prep_time: Number   // Optional minutes
}
```

### Indexes

For optimal performance, these indexes are created:
```javascript
db.recipes.createIndex({ "title": 1 })
db.recipes.createIndex({ "ingredients.item": 1 })
db.recipes.createIndex({ "oven": 1 })
db.recipes.createIndex({ "stove": 1 })
db.recipes.createIndex({ "tags": 1 })
```

## Frontend Implementation

### Form Fields
The AddRecipe.vue component now has 4 separate fields:

```vue
<template>
  <div class="ingredient-inputs">
    <input v-model="currentIngredient.quantity" placeholder="1" />
    <input v-model="currentIngredient.unit" placeholder="cup" />
    <input v-model="currentIngredient.item" placeholder="flour" />
    <input v-model="currentIngredient.original" placeholder="Original (optional)" />
  </div>
</template>

<script>
const currentIngredient = ref({
  quantity: '',
  unit: '',
  item: '',
  original: ''
})

function addIngredient() {
  // Auto-generate original if not provided
  const formatted = formatIngredient(currentIngredient.value)
  ingredients.value.push(formatted)
}

function formatIngredient(ing) {
  if (ing.original) {
    return ing
  }
  
  // Auto-generate from parts
  const parts = [ing.quantity, ing.unit, ing.item].filter(Boolean)
  return {
    ...ing,
    original: parts.join(' ')
  }
}
</script>
```

### Fuzzy Matching
As users type in the `item` field, suggestions appear:
```javascript
function onIngredientInput() {
  const input = currentIngredient.value.item.toLowerCase()
  if (input.length < 2) {
    fuzzyMatches.value = []
    return
  }
  
  fuzzyMatches.value = allIngredients.value
    .filter(ing => calculateSimilarity(input, ing) > 0.6)
    .slice(0, 5)
}
```

## Troubleshooting

### Issue: Old format ingredients appear
**Solution:** Run migration script:
```bash
python3 migrate_structured_ingredients.py
```

### Issue: Quantities not summing in grocery list
**Check:** Ensure ingredients have valid quantity fields:
```javascript
// ✗ Won't sum
{ item: "flour", original: "some flour" }

// ✓ Will sum
{ quantity: "2", unit: "cups", item: "flour", original: "2 cups flour" }
```

### Issue: Duplicate ingredients in list
**Check:** Item names must match exactly (case-insensitive):
```javascript
// These are treated as different:
{ item: "yellow onion" }  
{ item: "onion" }

// These are treated as same:
{ item: "garlic" }
{ item: "Garlic" }
```

## Testing

### Unit Tests
```bash
# Test ingredient parser
python3 -c "from ingredient_parser import parse_ingredient; print(parse_ingredient('1 cup flour'))"

# Test MongoDB operations
python3 -m pytest tests/test_mongodb_integration.py

# Test frontend
cd vue-frontend && npm test
```

### Manual Testing
1. Add recipe with structured ingredients
2. Generate dinner menu for 5 days
3. Verify grocery list sums quantities correctly
4. Check fuzzy matching works in UI

## Performance Notes

- **Aggregation**: O(n) where n = number of recipes × avg ingredients per recipe
- **Search by item**: O(log n) with index on `ingredients.item`
- **Parsing**: ~0.5ms per ingredient
- **Frontend fuzzy match**: O(m) where m = unique ingredients (~100-500)

## Future Enhancements

1. **Smart Parsing Improvements**
   - Better handling of preparation notes ("minced", "diced", "chopped")
   - Recognition of brand names
   - Temperature ranges

2. **Advanced Features**
   - Recipe scaling with unit conversion (cups ↔ ml)
   - Ingredient substitutions database
   - Nutrition API integration
   - Shopping list organization by store section

3. **Data Quality**
   - Automatic duplicate detection
   - Ingredient normalization suggestions
   - Spelling correction

## References

- [MongoDB Manual](https://docs.mongodb.com/)
- [Vue.js 3 Documentation](https://vuejs.org/)
- [Ingredient Parser Source](ingredient_parser.py)
- [Migration Script](migrate_structured_ingredients.py)
