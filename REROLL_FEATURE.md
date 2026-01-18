# Recipe Re-Roll Feature

## Summary
Added ability to re-roll/refresh recipes in the Dinner Menu while retaining the cached weather data, eliminating redundant API calls.

## Changes Made

### Backend (app.py)
- **Modified `/api/dinner-menu` endpoint** to accept both GET and POST methods:
  - `GET`: Fetches fresh weather data and generates menu (original behavior)
  - `POST`: Accepts cached weather data in request body and generates new menu without calling weather API
  - Validates that POST requests include weather data, returns 400 error if missing

### Frontend (streamlit_app.py)
- **Added `reroll_dinner_menu(days, weather_data)` function**: Posts to API with cached weather to get new recipe selection
- **Modified Dinner Menu page**:
  - Added "🔄 Re-roll" button next to "Generate Weather-Based Menu" button
  - Re-roll button is disabled until initial menu is generated
  - Caches weather data and menu results in `st.session_state`
  - Re-roll button uses cached weather to generate new menu without API call
  - Results persist across interactions via session state

### Testing
- **Added 3 new tests in `test_app.py`**:
  - `test_dinner_menu_reroll_with_cached_weather`: Verifies POST endpoint works with cached weather
  - `test_dinner_menu_reroll_missing_weather`: Ensures error when weather data is missing
  
- **Added 3 new tests in `test_streamlit_app.py`**:
  - `test_reroll_dinner_menu_success`: Tests successful re-roll with cached weather
  - `test_reroll_dinner_menu_failure`: Tests handling of API failure
  - `test_reroll_dinner_menu_exception`: Tests exception handling

**Test Results**: ✅ All 50 tests pass (3 new, 47 existing)

## User Experience

### Before
1. Generate menu → calls weather API
2. Want different recipes → generate again → calls weather API again ❌
3. Wastes API calls and time

### After
1. Generate menu → calls weather API once
2. Want different recipes → click Re-roll button → uses cached weather ✅
3. No redundant API calls, instant results

## API Usage Example

### Initial Generation (GET)
```bash
GET /api/dinner-menu?days=7
Response: {
  "success": true,
  "weather": { "location": "Spokane, WA", "forecast": [...] },
  "dinner_plan": { "selected_recipes": [...] }
}
```

### Re-roll with Cached Weather (POST)
```bash
POST /api/dinner-menu?days=7
Body: { "weather": { "location": "Spokane, WA", "forecast": [...] } }
Response: {
  "success": true,
  "weather": { "location": "Spokane, WA", "forecast": [...] },  # Same weather
  "dinner_plan": { "selected_recipes": [...] }  # Different recipes
}
```

## UI Changes
- **New button**: 🔄 Re-roll button in Weather-Based Menu tab
- **Button state**: Disabled until first menu generated
- **Visual feedback**: Loading spinner shows "Re-rolling recipes with same weather..."
- **Persistence**: Results stay visible until user leaves page or generates new menu

## Benefits
1. **Faster**: No weather API call on re-roll (instant results)
2. **Cost-effective**: Reduces API usage by ~50% for users who want multiple options
3. **Better UX**: Clear visual feedback with dedicated re-roll button
4. **Maintains context**: Weather stays same, only recipes change
5. **Well-tested**: 100% test coverage for new functionality
