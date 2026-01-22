# Dinner Menu Planner - Full Stack Application

A complete dinner menu planning system with Flask API backend and Streamlit frontend.

## Features

- 📋 Recipe Management (add, view, delete recipes)
- 🌤️ Weather-based menu planning
- 🍲 Smart recipe selection based on temperature
- ⚡ Quick menu generation without weather
- 🎨 Beautiful Streamlit UI

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

Set your RapidAPI weather key:
```bash
export RAPID_API_FORECAST_KEY="your_api_key_here"
```

## Running the Application

### Option 1: Using the startup script (Recommended)
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

This will start both the Flask API and Streamlit frontend automatically.

### Option 2: Manual startup

**Terminal 1 - Start the Flask API:**
```bash
python app.py
```

**Terminal 2 - Start the Streamlit frontend:**
```bash
streamlit run scripts/streamlit_app.py
```

## Access the Application

- **Streamlit Frontend:** http://localhost:8501
- **Flask API:** http://localhost:5000

## Pages

### 🏠 Home
- Quick overview with metrics
- Quick menu generation
- Weather check

### 📋 View Recipes
- Browse all recipes
- Filter by oven/stove requirements
- Search functionality
- Delete recipes

### ➕ Add Recipe
- Add new recipes with ingredients
- Specify cooking requirements
- Set portions and date

### 🌤️ Weather
- View 1-14 day forecast
- Temperature tracking

### 🍲 Dinner Menu
- **Weather-Based:** Considers temperature (excludes oven recipes when > 90°F)
- **Quick Menu:** Fast random selection without weather check

## API Endpoints

See [API_README.md](API_README.md) for detailed API documentation.

## Project Structure

```
dinner-menu/
├── app.py                  # Flask API
├── streamlit_app.py        # Streamlit frontend
├── dinner_menu.py          # Original CLI app
├── add-recipe.py           # Original recipe management CLI
├── recipes.json            # Recipe database
├── requirements.txt        # Python dependencies
├── requirements-test.txt   # Test dependencies
├── start.sh               # Startup script
├── run_tests.sh           # Test runner script
├── tests/                 # Test suite
│   ├── test_app.py        # Flask API unit tests
│   ├── test_streamlit_app.py  # Streamlit unit tests
│   ├── test_dinner_menu.py    # Core logic unit tests
│   ├── test_add_recipe.py     # Recipe management unit tests
│   └── test_e2e.py        # End-to-end integration tests
└── README.md              # This file
```

## Testing

The project includes comprehensive test coverage with **automatic data isolation** to protect production data.

### Data Protection

**Production data is automatically protected during tests:**
- `recipes.json` is never modified by tests
- `backups/` directory is never touched by tests
- Tests use isolated test data in `tests/test_data/` (auto-created and cleaned up)

See [docs/DATA_PROTECTION.md](docs/DATA_PROTECTION.md) for complete details.

### Running Tests

```bash
# Run all tests with comprehensive checks
./scripts/testing/run_all_tests.sh

# Run pytest tests only
./scripts/testing/run_tests.sh

# Quick system health check
./scripts/testing/quick_test.sh

# Run specific test file
python -m pytest tests/test_e2e.py -v

# Run with coverage report
python -m pytest tests/ -v --cov=. --cov-report=html
```

### Test Types

- **Unit Tests** (`test_app.py`, `test_streamlit_app.py`, `test_dinner_menu.py`, `test_add_recipe.py`)
  - Test individual components in isolation
  - Use mocks to avoid external dependencies
  - Fast execution

- **End-to-End Tests** (`test_e2e.py`)
  - Test complete user workflows
  - Test API integration between components
  - Verify full request/response cycles
  - Examples:
    - Complete recipe CRUD workflow
    - Weather integration with menu generation
    - Grocery list generation
    - Error handling scenarios

All tests run automatically in CI/CD pipeline before Docker image builds.

## Tips

- Recipes are randomly shuffled each time you generate a menu
- High temperature days (>90°F) automatically exclude oven recipes
- Use the quick menu for faster results without weather API calls
- All recipe changes are automatically backed up in the `backups/` folder
