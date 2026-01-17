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
chmod +x start.sh
./start.sh
```

This will start both the Flask API and Streamlit frontend automatically.

### Option 2: Manual startup

**Terminal 1 - Start the Flask API:**
```bash
python app.py
```

**Terminal 2 - Start the Streamlit frontend:**
```bash
streamlit run streamlit_app.py
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
├── start.sh               # Startup script
└── README.md              # This file
```

## Tips

- Recipes are randomly shuffled each time you generate a menu
- High temperature days (>90°F) automatically exclude oven recipes
- Use the quick menu for faster results without weather API calls
- All recipe changes are automatically backed up in the `backups/` folder
