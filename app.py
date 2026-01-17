from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import shutil
from datetime import datetime
import requests
import time
import random
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configuration
RECIPES_FILE = "recipes.json"
BACKUP_DIR = "backups"

# Logging configuration
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/api.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('Dinner Menu API startup')

# Request logging middleware
@app.before_request
def log_request():
    app.logger.info(f'{request.method} {request.path} - {request.remote_addr}')

@app.after_request
def log_response(response):
    app.logger.info(f'{request.method} {request.path} - Status: {response.status_code}')
    return response

# ============= Recipe Management Functions =============

def load_recipes():
    """Load recipes from the JSON file or return empty list if missing."""
    if os.path.exists(RECIPES_FILE):
        with open(RECIPES_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_recipes(data):
    """Save recipes to JSON, with a backup of the old file."""
    if os.path.exists(RECIPES_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"recipes_{timestamp}.json")
        shutil.copy(RECIPES_FILE, backup_file)

    with open(RECIPES_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ============= Weather & Dinner Menu Functions =============

def get_weather_forecast(days):
    """Fetch weather forecast for specified days."""
    api_key = os.getenv('RAPID_API_FORECAST_KEY')
    
    if not api_key:
        raise ValueError("RAPID_API_FORECAST_KEY environment variable not set")
    
    url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
    querystring = {"q": "Spokane", "days": days}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "weatherapi-com.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    data = response.json()
    
    city = data["location"]["name"]
    region = data["location"]["region"]
    
    formatted = [
        {
            "day": datetime.strptime(day['date'], '%Y-%m-%d').strftime('%A'),
            "date": day['date'],
            "temp": day['day']['maxtemp_f']
        }
        for day in data["forecast"]["forecastday"]
    ]
    
    return {
        "location": f"{city}, {region}",
        "forecast": formatted
    }

def generate_grocery_list(recipes):
    """Generate a consolidated grocery list from selected recipes."""
    all_ingredients = []
    for recipe in recipes:
        all_ingredients.extend(recipe.get('ingredients', []))
    
    # Count ingredient occurrences
    ingredient_counts = {}
    for ingredient in all_ingredients:
        ingredient_lower = ingredient.lower().strip()
        ingredient_counts[ingredient_lower] = ingredient_counts.get(ingredient_lower, 0) + 1
    
    # Sort alphabetically
    grocery_list = sorted([
        {"ingredient": ing, "count": count}
        for ing, count in ingredient_counts.items()
    ], key=lambda x: x['ingredient'])
    
    return grocery_list

def select_dinner_recipes(weather_data, days):
    """Select recipes based on weather and days needed."""
    temps = [day['temp'] for day in weather_data['forecast']]
    too_hot = any(temp > 90 for temp in temps)
    
    recipes = load_recipes()
    
    available_recipes = [r for r in recipes if not (too_hot and r.get("oven", False))]
    random.shuffle(available_recipes)
    
    selected_recipes = []
    total_portions = 0
    
    for recipe in available_recipes:
        portions = int(recipe.get("portions", "1"))
        selected_recipes.append(recipe)
        total_portions += portions
        
        if total_portions >= days:
            break
    
    grocery_list = generate_grocery_list(selected_recipes)
    
    return {
        "selected_recipes": selected_recipes,
        "total_portions": total_portions,
        "days_requested": days,
        "too_hot_for_oven": too_hot,
        "grocery_list": grocery_list
    }

# ============= API Routes =============

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    app.logger.info('Health check requested')
    return jsonify({"status": "healthy", "message": "Dinner Menu API is running"})

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes."""
    app.logger.info('Fetching all recipes')
    recipes = load_recipes()
    app.logger.info(f'Returned {len(recipes)} recipes')
    return jsonify({
        "success": True,
        "count": len(recipes),
        "recipes": recipes
    })

@app.route('/api/recipes', methods=['POST'])
def add_recipe():
    """Add a new recipe."""
    try:
        data = request.get_json()
        app.logger.info(f'Adding new recipe: {data.get("title", "Unknown")}')
        
        # Validate required fields
        required_fields = ['title', 'ingredients']
        for field in required_fields:
            if field not in data:
                app.logger.warning(f'Missing required field: {field}')
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Create recipe object
        recipe = {
            "title": data['title'],
            "date": data.get('date', datetime.now().strftime('%Y-%m-%d')),
            "ingredients": data['ingredients'] if isinstance(data['ingredients'], list) else [i.strip() for i in data['ingredients'].split(',')],
            "oven": data.get('oven', False),
            "stove": data.get('stove', False),
            "portions": data.get('portions', "1")
        }
        
        # Load, add, and save
        recipes = load_recipes()
        recipes.append(recipe)
        save_recipes(recipes)
        app.logger.info(f'Recipe "{recipe["title"]}" added successfully')
        
        return jsonify({
            "success": True,
            "message": "Recipe added successfully",
            "recipe": recipe
        }), 201
        
    except Exception as e:
        app.logger.error(f'Error adding recipe: {str(e)}')
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/recipes/<int:index>', methods=['DELETE'])
def delete_recipe(index):
    """Delete a recipe by index."""
    try:
        app.logger.info(f'Attempting to delete recipe at index {index}')
        recipes = load_recipes()
        
        if index < 0 or index >= len(recipes):
            app.logger.warning(f'Recipe index {index} out of range')
            return jsonify({
                "success": False,
                "error": "Recipe index out of range"
            }), 404
        
        deleted_recipe = recipes.pop(index)
        save_recipes(recipes)
        app.logger.info(f'Recipe "{deleted_recipe["title"]}" deleted successfully')
        
        return jsonify({
            "success": True,
            "message": "Recipe deleted successfully",
            "deleted_recipe": deleted_recipe
        })
        
    except Exception as e:
        app.logger.error(f'Error deleting recipe: {str(e)}')
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Get weather forecast."""
    try:
        days = request.args.get('days', default=7, type=int)
        app.logger.info(f'Fetching weather forecast for {days} days')
        
        if days < 1 or days > 14:
            app.logger.warning(f'Invalid days requested: {days}')
            return jsonify({
                "success": False,
                "error": "Days must be between 1 and 14"
            }), 400
        
        weather_data = get_weather_forecast(days)
        app.logger.info(f'Weather forecast retrieved successfully')
        
        return jsonify({
            "success": True,
            "weather": weather_data
        })
        
    except Exception as e:
        app.logger.error(f'Error fetching weather: {str(e)}')
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dinner-menu', methods=['GET'])
def get_dinner_menu():
    """Get dinner menu suggestions based on weather and days."""
    try:
        days = request.args.get('days', default=7, type=int)
        app.logger.info(f'Generating dinner menu for {days} days with weather')
        
        if days < 1 or days > 14:
            app.logger.warning(f'Invalid days requested: {days}')
            return jsonify({
                "success": False,
                "error": "Days must be between 1 and 14"
            }), 400
        
        # Get weather forecast
        weather_data = get_weather_forecast(days)
        
        # Select recipes
        dinner_plan = select_dinner_recipes(weather_data, days)
        app.logger.info(f'Selected {len(dinner_plan["selected_recipes"])} recipes for dinner menu')
        
        return jsonify({
            "success": True,
            "weather": weather_data,
            "dinner_plan": dinner_plan
        })
        
    except Exception as e:
        app.logger.error(f'Error generating dinner menu: {str(e)}')
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dinner-menu/quick', methods=['GET'])
def get_quick_dinner_menu():
    """Get dinner menu suggestions without weather (random selection)."""
    try:
        days = request.args.get('days', default=7, type=int)
        app.logger.info(f'Generating quick dinner menu for {days} days')
        
        if days < 1 or days > 14:
            app.logger.warning(f'Invalid days requested: {days}')
            return jsonify({
                "success": False,
                "error": "Days must be between 1 and 14"
            }), 400
        
        recipes = load_recipes()
        random.shuffle(recipes)
        
        selected_recipes = []
        total_portions = 0
        
        for recipe in recipes:
            portions = int(recipe.get("portions", "1"))
            selected_recipes.append(recipe)
            total_portions += portions
            
            if total_portions >= days:
                break
        
        grocery_list = generate_grocery_list(selected_recipes)
        app.logger.info(f'Selected {len(selected_recipes)} recipes for quick menu')
        
        return jsonify({
            "success": True,
            "dinner_plan": {
                "selected_recipes": selected_recipes,
                "total_portions": total_portions,
                "days_requested": days,
                "grocery_list": grocery_list
            }
        })
        
    except Exception as e:
        app.logger.error(f'Error generating quick menu: {str(e)}')
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.logger.info('Starting Flask API server')
    app.run(debug=True, host='0.0.0.0', port=5000)
