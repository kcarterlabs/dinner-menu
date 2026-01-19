# Ingredient Suggestion Feature

## Overview
The ingredient suggestion feature helps normalize ingredient names across recipes by providing autocomplete suggestions based on existing ingredients in the recipe database.

## Features

### 1. **Automatic Ingredient Extraction**
- Extracts all unique ingredients from existing recipes
- Normalizes to lowercase for consistent matching
- Caches results in session state for performance

### 2. **Fuzzy Matching Algorithm**
Uses Python's `SequenceMatcher` from `difflib` to find similar ingredients:
- **Substring matching**: Exact substring matches get priority (score: 1.0)
- **Fuzzy matching**: Uses similarity ratio with configurable threshold (default: 0.6)
- Returns top 10 most similar matches, sorted by similarity score

### 3. **Interactive UI**
Located below the "Add Recipe" form:
- **Search box**: Type 2+ characters to see suggestions
- **Visual feedback**: 
  - Blue info box shows number of matches found
  - Warning if no matches (new ingredient)
  - Caption prompts for more characters if input too short
- **Clickable buttons**: Display matching ingredients in 3-column grid
- **Copy helper**: Clicking a button shows how to copy the exact ingredient text

## Usage Example

### Adding a Recipe with Ingredient Suggestions

1. Navigate to **➕ Add Recipe** page
2. Fill in recipe title, oven/stove, portions, and date
3. Scroll to **🔍 Ingredient Suggestion Tool**
4. Type an ingredient (e.g., "tomato")
5. View suggested matches:
   ```
   💡 Found 8 similar ingredient(s) in existing recipes:
   📋 2 tablespoons tomato paste
   📋 8 oz. tomato sauce
   📋 1 (28 oz.) can diced tomatoes
   ...
   ```
6. Click a button to see the exact text to copy
7. Paste into the ingredients text area above

### Example Matches

**Input: "pasta"**
- `1/2 lb. uncooked macaroni`
- `8 oz. pasta`
- `pasta`
- `1 lb. penne pasta`

**Input: "onio"** (typo)
- `1 yellow onion`
- `1 medium yellow onion, diced`
- `2 small onions`

**Input: "garli"** (typo)
- `5 cloves garlic, minced`
- `2 cloves garlic`
- `1/2 tsp garlic powder`

## Technical Implementation

### Functions

#### `get_all_ingredients()`
```python
def get_all_ingredients():
    """Extract all unique ingredients from existing recipes"""
    recipes = get_recipes()
    ingredients_set = set()
    
    for recipe in recipes:
        for ingredient in recipe.get('ingredients', []):
            ingredient_lower = ingredient.lower().strip()
            ingredients_set.add(ingredient_lower)
    
    return sorted(list(ingredients_set))
```

#### `find_similar_ingredients(input_text, all_ingredients, threshold=0.6)`
```python
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
```

### Session State Management
- **`st.session_state.all_ingredients`**: Cached list of all ingredients
  - Loaded once on page load
  - Cleared after successfully adding a new recipe
  - Prevents redundant API calls

### UI Components
1. **Help text in form**: Tooltip on ingredients text area
2. **Search input**: Text input with placeholder
3. **Results display**: Info/warning boxes with match count
4. **Suggestion buttons**: 3-column grid of clickable ingredient buttons

## Benefits

1. **Consistency**: Reduces duplicate ingredients with different capitalizations
2. **Efficiency**: Faster recipe entry by reusing existing ingredient formats
3. **Data Quality**: Maintains cleaner, more normalized recipe database
4. **User Experience**: Prevents typos and format inconsistencies
5. **Discovery**: Users can see what ingredients are already in their collection

## Future Enhancements

Potential improvements:
- [ ] Auto-extract quantity vs ingredient name (e.g., "2 cups" vs "flour")
- [ ] Suggest quantity normalization (cups vs tablespoons)
- [ ] Ingredient categorization (proteins, vegetables, spices, etc.)
- [ ] Direct click-to-add (bypass copy/paste)
- [ ] Ingredient frequency analytics (most common ingredients)
- [ ] Synonym detection (e.g., "scallions" = "green onions")
