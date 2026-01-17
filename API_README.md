# Dinner Menu API

Flask API for managing recipes and generating dinner menus based on weather forecasts.

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

```bash
export RAPID_API_FORECAST_KEY="your_api_key_here"
```

## Running the API

```bash
python app.py
```

The API will run on `http://localhost:5000`

## API Endpoints

### Health Check
- **GET** `/api/health` - Check API status

### Recipe Management

- **GET** `/api/recipes` - Get all recipes
  ```json
  {
    "success": true,
    "count": 10,
    "recipes": [...]
  }
  ```

- **POST** `/api/recipes` - Add a new recipe
  ```json
  {
    "title": "Spaghetti Carbonara",
    "ingredients": ["pasta", "eggs", "bacon", "parmesan"],
    "oven": false,
    "stove": true,
    "portions": "4"
  }
  ```

- **DELETE** `/api/recipes/<index>` - Delete a recipe by index

### Weather

- **GET** `/api/weather?days=7` - Get weather forecast
  - Query params: `days` (1-14, default: 7)

### Dinner Menu

- **GET** `/api/dinner-menu?days=7` - Get dinner menu with weather consideration
  - Query params: `days` (1-14, default: 7)
  - Returns weather forecast and selected recipes
  - Automatically excludes oven recipes when temperature > 90°F

- **GET** `/api/dinner-menu/quick?days=7` - Get dinner menu without weather check
  - Query params: `days` (1-14, default: 7)
  - Fast random selection without weather API call

## Example Usage

### Add a recipe
```bash
curl -X POST http://localhost:5000/api/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Chicken Stir Fry",
    "ingredients": ["chicken", "vegetables", "soy sauce"],
    "oven": false,
    "stove": true,
    "portions": "3"
  }'
```

### Get dinner menu
```bash
curl http://localhost:5000/api/dinner-menu?days=5
```

### Get all recipes
```bash
curl http://localhost:5000/api/recipes
```

## CORS

CORS is enabled for all origins to allow frontend applications to access the API.
