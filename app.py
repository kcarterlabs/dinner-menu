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
from ingredient_parser import parse_ingredient

app = Flask(__name__)
CORS(app)

# Configuration
RECIPES_FILE = "recipes.json"
BACKUP_DIR = "backups"
WEATHER_LOCATION = os.getenv('WEATHER_LOCATION', 'Spokane')

# Logging
if not os.path.exists('logs'):
    try:
        os.makedirs('logs')
    except (OSError, PermissionError):
        pass

try:
    file_handler = RotatingFileHandler('logs/api.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Dinner Menu API startup')
except (OSError, PermissionError):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

# MongoDB initialization (with fallback)
try:
    from db import RecipeDB, convert_objectid_to_str
    recipe_db = RecipeDB()
    app.logger.info('MongoDB initialized')
    USE_MONGODB = True
except Exception as e:
    app.logger.warning(f'MongoDB not available: {e}')
    recipe_db = None
    USE_MONGODB = False

# Recipe Management
def load_recipes():
    if USE_MONGODB and recipe_db:
        try:
            recipes = recipe_db.get_all_recipes()
            return convert_objectid_to_str(recipes)
        except Exception as e:
            app.logger.error(f"MongoDB error: {e}")
    
    if os.path.exists(RECIPES_FILE):
        with open(RECIPES_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_recipes(data):
    if os.path.exists(RECIPES_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"recipes_{timestamp}.json")
        shutil.copy(RECIPES_FILE, backup_file)
    
    with open(RECIPES_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Weather
def get_weather_forecast(days):
    api_key = os.getenv('RAPID_API_FORECAST_KEY')
    if not api_key:
        raise ValueError("RAPID_API_FORECAST_KEY not set")
    
    url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
    response = requests.get(url, headers={
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "weatherapi-com.p.rapidapi.com"
    }, params={"q": WEATHER_LOCATION, "days": days})
    response.raise_for_status()
    data = response.json()
    
    formatted = [{
        "day": datetime.strptime(day['date'], '%Y-%m-%d').strftime('%A'),
        "date": day['date'],
        "temp": day['day']['maxtemp_f']
    } for day in data["forecast"]["forecastday"]]
    
    return {
        "location": f"{data['location']['name']}, {data['location']['region']}",
        "forecast": formatted
    }

# Grocery List
def generate_grocery_list(recipes):
    """Generate aggregated grocery list from recipes, summing quantities by item and unit"""
    if USE_MONGODB and recipe_db:
        try:
            recipe_ids = [r.get('_id') for r in recipes if '_id' in r]
            if recipe_ids:
                return recipe_db.aggregate_ingredients(recipe_ids)
        except Exception as e:
            app.logger.warning(f"MongoDB aggregation failed: {e}")
    
    # Fallback: aggregate ingredients manually with quantity summing
    from ingredient_parser import quantity_to_float, normalize_unit
    from collections import defaultdict
    
    # Group by (item, unit) and collect quantities
    ingredient_groups = defaultdict(lambda: {'quantities': [], 'recipes': set()})
    
    for recipe in recipes:
        recipe_title = recipe.get('title', 'Unknown')
        ingredients_list = recipe.get('ingredients', [])
        
        for ingredient in ingredients_list:
            if isinstance(ingredient, dict):
                # Structured ingredient
                item = ingredient.get('item', '').lower().strip()
                unit = normalize_unit(ingredient.get('unit', '').lower().strip())
                quantity = ingredient.get('quantity', '')
            else:
                # Legacy string format - try to parse
                ingredient_str = str(ingredient)
                parsed = parse_ingredient(ingredient_str)
                item = parsed.get('item', '').lower().strip()
                unit = normalize_unit(parsed.get('unit', '').lower().strip())
                quantity = parsed.get('quantity', '')
            
            if not item:
                continue
                
            # Skip non-ingredient items
            exclude_phrases = ['look it up', 'see recipe', 'check recipe', 'refer to']
            if any(phrase in item for phrase in exclude_phrases):
                continue
            
            key = (item, unit)
            ingredient_groups[key]['quantities'].append(quantity)
            ingredient_groups[key]['recipes'].add(recipe_title)
    
    # Sum quantities and format results
    aggregated = []
    for (item, unit), data in sorted(ingredient_groups.items()):
        quantities = data['quantities']
        recipes = list(data['recipes'])
        
        # Sum all quantities
        total = sum(quantity_to_float(q) for q in quantities if q)
        
        # Format the result
        if total > 0:
            # Format quantity nicely
            if total == int(total):
                qty_str = str(int(total))
            else:
                qty_str = f"{total:.2f}".rstrip('0').rstrip('.')
            
            if unit:
                ingredient_str = f"{qty_str} {unit} {item}"
            else:
                ingredient_str = f"{qty_str} {item}"
        else:
            # No quantity found, just show count and item
            if unit:
                ingredient_str = f"{unit} {item}"
            else:
                ingredient_str = item
        
        aggregated.append({
            "ingredient": ingredient_str,
            "item": item,
            "quantity": total if total > 0 else None,
            "unit": unit,
            "count": len(quantities),  # How many times it appears
            "recipes": recipes
        })
    
    return aggregated


# Recipe Selection
def select_dinner_recipes(weather_data, days, reroll_index=None, current_menu=None):
    temps = [day['temp'] for day in weather_data['forecast']]
    too_hot = any(temp > 90 for temp in temps)
    recipes = load_recipes()
    
    if reroll_index is not None and current_menu:
        selected_recipes = current_menu.copy()
        available = [r for r in recipes if not (too_hot and r.get("oven", False)) and r not in current_menu]
        random.shuffle(available)
        if available and 0 <= reroll_index < len(selected_recipes):
            selected_recipes[reroll_index] = available[0]
        total_portions = sum(int(r.get("portions", "1")) for r in selected_recipes)
    else:
        available = [r for r in recipes if not (too_hot and r.get("oven", False))]
        random.shuffle(available)
        selected_recipes = []
        total_portions = 0
        for recipe in available:
            if total_portions >= days:
                break
            portions = int(recipe.get("portions", "1"))
            selected_recipes.append(recipe)
            total_portions += portions
    
    grocery_list = generate_grocery_list(selected_recipes)
    
    return {
        "selected_recipes": selected_recipes,
        "total_portions": total_portions,
        "days_requested": days,
        "too_hot_for_oven": too_hot,
        "grocery_list": grocery_list
    }

# API Routes
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "Dinner Menu API is running"})

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    try:
        if USE_MONGODB:
            # Get recipes from MongoDB
            recipes = recipe_db.get_all_recipes()
            # Convert ObjectId to string for JSON serialization
            recipes_json = [convert_objectid_to_str(recipe) for recipe in recipes]
            return jsonify({"success": True, "count": len(recipes_json), "recipes": recipes_json})
        else:
            # Fallback to JSON file (legacy)
            recipes = load_recipes()
            return jsonify({"success": True, "count": len(recipes), "recipes": recipes})
    except Exception as e:
        app.logger.error(f"Error getting recipes: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recipes', methods=['POST'])
def add_recipe():
    try:
        data = request.get_json()
        if 'title' not in data or 'ingredients' not in data:
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        # Process ingredients - support both structured and string formats
        ingredients = data.get('ingredients', [])
        processed_ingredients = []
        
        for ing in ingredients:
            if isinstance(ing, dict):
                # Already structured format from new frontend
                processed_ingredients.append(ing)
            elif isinstance(ing, str):
                # Legacy string format - parse it
                from ingredient_parser import parse_ingredient
                processed_ingredients.append(parse_ingredient(ing.strip()))
            else:
                processed_ingredients.append({'item': str(ing), 'quantity': '', 'unit': '', 'original': str(ing)})
        
        recipe = {
            "title": data['title'],
            "date": data.get('date', datetime.now().strftime('%Y-%m-%d')),
            "ingredients": processed_ingredients,
            "oven": data.get('oven', False),
            "stove": data.get('stove', False),
            "portions": data.get('portions', "1"),
            "image": data.get('image')  # Base64 encoded image string
        }
        
        # Save to MongoDB if available
        if USE_MONGODB and recipe_db:
            try:
                recipe_id = recipe_db.create_recipe(recipe.copy())  # Pass a copy to avoid mutation
                recipe['_id'] = recipe_id
                # Add string versions of timestamps for JSON serialization
                recipe['created_at'] = datetime.now().strftime('%Y-%m-%d')
                recipe['updated_at'] = datetime.now().strftime('%Y-%m-%d')
                app.logger.info(f"Recipe '{recipe['title']}' saved to MongoDB with ID: {recipe_id}")
            except Exception as e:
                app.logger.error(f"Failed to save to MongoDB: {e}, falling back to JSON")
        else:
            app.logger.warning(f"MongoDB not available: USE_MONGODB={USE_MONGODB}, recipe_db={recipe_db}")
        
        # Also save to JSON file as backup
        recipes = load_recipes()
        recipes.append(recipe)
        save_recipes(recipes)
        
        # Convert ObjectIds and datetimes for JSON response
        recipe_response = convert_objectid_to_str(recipe)
        
        return jsonify({"success": True, "message": "Recipe added", "recipe": recipe_response}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recipes/<recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    try:
        if USE_MONGODB:
            # Delete from MongoDB
            if recipe_db.delete_recipe(recipe_id):
                return jsonify({"success": True, "message": "Recipe deleted"})
            else:
                return jsonify({"success": False, "error": "Recipe not found"}), 404
        else:
            # Fallback to JSON file (legacy)
            recipes = load_recipes()
            # Find recipe by _id or title
            recipe_index = next((i for i, r in enumerate(recipes) if r.get('_id') == recipe_id or str(i) == recipe_id), None)
            if recipe_index is None:
                return jsonify({"success": False, "error": "Recipe not found"}), 404
            
            deleted = recipes.pop(recipe_index)
            save_recipes(recipes)
            return jsonify({"success": True, "message": "Deleted", "deleted_recipe": deleted})
    except Exception as e:
        app.logger.error(f"Error deleting recipe {recipe_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recipes/<recipe_id>/image', methods=['PUT'])
def update_recipe_image(recipe_id):
    """Update or add image to existing recipe"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        # Allow null/None to remove image
        if image_data is None:
            if USE_MONGODB:
                if recipe_db.update_recipe(recipe_id, {"image": None}):
                    return jsonify({"success": True, "message": "Image removed"})
                else:
                    return jsonify({"success": False, "error": "Recipe not found"}), 404
            else:
                recipes = load_recipes()
                recipe_index = next((i for i, r in enumerate(recipes) if r.get('_id') == recipe_id), None)
                if recipe_index is None:
                    return jsonify({"success": False, "error": "Recipe not found"}), 404
                
                recipes[recipe_index]['image'] = None
                save_recipes(recipes)
                return jsonify({"success": True, "message": "Image removed"})
        
        if not image_data:
            return jsonify({"success": False, "error": "No image data provided"}), 400
        
        # Validate base64 image (basic check)
        if not image_data.startswith('data:image/'):
            return jsonify({"success": False, "error": "Invalid image format"}), 400
        
        if USE_MONGODB:
            # Update MongoDB
            if recipe_db.update_recipe(recipe_id, {"image": image_data}):
                return jsonify({"success": True, "message": "Image updated"})
            else:
                return jsonify({"success": False, "error": "Recipe not found"}), 404
        else:
            # Fallback to JSON file
            recipes = load_recipes()
            recipe_index = next((i for i, r in enumerate(recipes) if r.get('_id') == recipe_id), None)
            if recipe_index is None:
                return jsonify({"success": False, "error": "Recipe not found"}), 404
            
            recipes[recipe_index]['image'] = image_data
            save_recipes(recipes)
            return jsonify({"success": True, "message": "Image updated"})
    except Exception as e:
        app.logger.error(f"Error updating recipe image {recipe_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/parse-ingredients', methods=['POST'])
def parse_ingredients():
    """Parse a list of ingredient strings into structured format"""
    try:
        data = request.get_json()
        raw_ingredients = data.get('ingredients', [])
        
        if not isinstance(raw_ingredients, list):
            return jsonify({"success": False, "error": "Ingredients must be a list"}), 400
        
        parsed_ingredients = []
        
        for raw_text in raw_ingredients:
            if not raw_text or not raw_text.strip():
                continue
                
            # Clean up the text - remove checkboxes, prices, etc.
            cleaned = raw_text.strip()
            # Remove checkbox symbols
            cleaned = cleaned.replace('▢', '').replace('☐', '').replace('□', '').strip()
            # Remove prices in parentheses (e.g., ($0.70))
            import re
            cleaned = re.sub(r'\s*\(\$[\d.]+\)', '', cleaned)
            # Remove leading dashes or bullets
            cleaned = re.sub(r'^[-•*]\s*', '', cleaned).strip()
            
            if not cleaned:
                continue
            
            # Parse the ingredient using existing parser
            parsed = parse_ingredient(cleaned)
            
            # Store both parsed and original
            ingredient = {
                'quantity': parsed.get('quantity', ''),
                'unit': parsed.get('unit', ''),
                'item': parsed.get('item', cleaned),  # Fallback to cleaned text
                'original': raw_text.strip()  # Preserve original input
            }
            
            parsed_ingredients.append(ingredient)
        
        return jsonify({
            "success": True,
            "parsed_ingredients": parsed_ingredients,
            "count": len(parsed_ingredients)
        })
        
    except Exception as e:
        app.logger.error(f"Error parsing ingredients: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        days = request.args.get('days', default=7, type=int)
        if days < 1 or days > 14:
            return jsonify({"success": False, "error": "Days must be 1-14"}), 400
        
        weather_data = get_weather_forecast(days)
        return jsonify({"success": True, "weather": weather_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dinner-menu', methods=['GET', 'POST'])
def get_dinner_menu():
    try:
        days = request.args.get('days', default=7, type=int)
        if days < 1 or days > 14:
            return jsonify({"success": False, "error": "Days must be 1-14"}), 400
        
        if request.method == 'POST':
            data = request.get_json()
            weather_data = data.get('weather')
            reroll_index = data.get('reroll_index')
            current_menu = data.get('current_menu', [])
            if not weather_data:
                return jsonify({"success": False, "error": "Weather required"}), 400
        else:
            weather_data = get_weather_forecast(days)
            reroll_index = None
            current_menu = []
        
        dinner_plan = select_dinner_recipes(weather_data, days, reroll_index, current_menu)
        return jsonify({"success": True, "weather": weather_data, "dinner_plan": dinner_plan})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dinner-menu/quick', methods=['GET'])
def get_quick_dinner_menu():
    try:
        days = request.args.get('days', default=7, type=int)
        if days < 1 or days > 14:
            return jsonify({"success": False, "error": "Days must be 1-14"}), 400
        
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
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
