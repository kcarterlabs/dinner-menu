# Individual Recipe Re-Roll Feature

## Overview
Enhanced the re-roll functionality to allow users to re-roll individual recipes while keeping others in the menu plan. This provides more granular control over meal planning.

## Changes Made

### 1. Backend API (`app.py`)

#### Updated `select_dinner_recipes()` function
- Added `exclude_indices` parameter to accept list of recipe indices to keep
- Modified logic to preserve recipes at specified indices
- Only re-randomizes remaining recipes to fill portions needed

```python
def select_dinner_recipes(weather_data, days, exclude_indices=None):
    """Select recipes based on weather and days needed.
    
    Args:
        weather_data: Weather forecast data
        days: Number of days to plan for
        exclude_indices: List of recipe indices to keep (not re-roll)
    """
```

#### Updated `/api/dinner-menu` endpoint
- Now accepts `exclude_indices` in POST request body
- Passes indices to `select_dinner_recipes()` function
- Logs whether keeping specific recipes or re-rolling all

### 2. Frontend (`streamlit_app.py`)

#### Updated `reroll_dinner_menu()` function
- Added `keep_indices` parameter for recipes to preserve
- Sends `exclude_indices` in API request when provided

#### Enhanced UI
- Removed global "Re-roll" button from top right
- Added individual 🔄 re-roll button on each recipe card
- Button appears next to recipe details in the expander
- Clicking re-rolls only that specific recipe, keeping all others
- Automatically updates session state with new menu
- Tracks recipe indices from original recipes.json for exclusion logic

### 3. Session State Management
- `st.session_state.weather_menu_result`: Stores current menu result
- `st.session_state.recipe_indices`: Maps selected recipes to their indices in recipes.json
- Updated on each generate/re-roll to maintain accurate tracking

### 4. Tests Updated

#### `tests/test_app.py`
- Updated `test_dinner_menu_reroll_with_cached_weather` to verify `exclude_indices=[]` passed
- Added `test_dinner_menu_reroll_single_recipe` to test keeping specific recipes

#### `tests/test_streamlit_app.py`
- Updated `test_reroll_dinner_menu_success` for new function signature  
- Added `test_reroll_single_recipe` to verify `keep_indices` parameter

## User Experience

### Before:
- Single "Re-roll" button that regenerated entire menu
- Had to re-roll all recipes even if you liked most of them

### After:
- Individual 🔄 button on each recipe card
- Click to re-roll just that one recipe
- All other recipes stay the same
- Weather data is cached, so no additional API calls

## Example Usage

1. User generates weather-based menu for 7 days
2. Gets 4 recipes: Recipe A, B, C, D
3. Likes A, B, and D but wants to change C
4. Clicks 🔄 button on Recipe C card
5. Recipe C is replaced with Recipe E
6. Final menu: Recipe A, B, E, D
7. Weather data and other recipes unchanged

## Technical Implementation

### Recipe Exclusion Logic
1. When re-rolling recipe at index N:
   - Build list of all OTHER indices: [0, 1, ..., N-1, N+1, ..., end]
   - Send as `exclude_indices` to API
2. API loads all recipes and keeps ones at excluded indices
3. Filters remaining recipes (weather + not already selected)
4. Randomizes and selects additional recipes
5. Returns combined list maintaining kept recipes

### Index Tracking
- On menu generation, map each selected recipe title to its index in `recipes.json`
- Store in `st.session_state.recipe_indices`
- Update after each re-roll by re-mapping titles to indices
- Ensures correct recipes are excluded even if recipes.json order changes

## Benefits

✅ **More Control**: Re-roll individual recipes without losing good selections  
✅ **Efficiency**: No need to regenerate entire menu multiple times  
✅ **Better UX**: Intuitive button placement right on recipe card  
✅ **API Efficiency**: Reuses cached weather data  
✅ **Flexible**: Can keep any combination of recipes

## Files Modified

- `app.py` - API endpoint and selection logic
- `streamlit_app.py` - UI and re-roll function  
- `tests/test_app.py` - Backend tests
- `tests/test_streamlit_app.py` - Frontend tests

## Testing

Run tests to validate:
```bash
python -m pytest tests/ -v
```

All tests pass with the new functionality.
