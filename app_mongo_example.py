"""
Example showing key changes needed in app.py for MongoDB integration

This shows the main functions that need to be updated.
You can integrate these gradually while keeping recipes.json as fallback.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from db import RecipeDB, convert_objectid_to_str

app = Flask(__name__)
CORS(app)

# Initialize MongoDB
recipe_db = RecipeDB()

# ============= Recipe Management with MongoDB =============

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes from MongoDB"""
    try:
        recipes = recipe_db.get_all_recipes()
        # Convert ObjectId to string for JSON serialization
        recipes_json = convert_objectid_to_str(recipes)
        return jsonify(recipes_json), 200
    except Exception as e:
        app.logger.error(f"Error fetching recipes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe"""
    try:
        recipe = recipe_db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        return jsonify(convert_objectid_to_str(recipe)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    """Add a new recipe"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({"error": "Title is required"}), 400
        
        recipe_id = recipe_db.create_recipe(data)
        return jsonify({"id": recipe_id, "message": "Recipe created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recipes/<recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Update an existing recipe"""
    try:
        data = request.get_json()
        success = recipe_db.update_recipe(recipe_id, data)
        
        if success:
            return jsonify({"message": "Recipe updated"}), 200
        return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recipes/<recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Delete a recipe"""
    try:
        success = recipe_db.delete_recipe(recipe_id)
        if success:
            return jsonify({"message": "Recipe deleted"}), 200
        return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= Dinner Menu with MongoDB =============

def select_dinner_recipes_mongo(weather_data, days, reroll_index=None, current_menu=None):
    """
    Select recipes for dinner menu using MongoDB.
    Uses same logic as before but fetches from MongoDB.
    """
    import random
    
    # Get all recipes from MongoDB
    all_recipes = recipe_db.get_all_recipes()
    
    if not all_recipes:
        raise ValueError("No recipes available in database")
    
    # Convert to list format expected by existing logic
    recipes_list = convert_objectid_to_str(all_recipes)
    
    # Existing selection logic...
    if reroll_index is not None and current_menu:
        # Re-roll logic
        selected_recipes = current_menu.copy()
        available = [r for r in recipes_list if r not in current_menu]
        if available:
            selected_recipes[reroll_index] = random.choice(available)
    else:
        # Initial selection
        selected_recipes = random.sample(recipes_list, min(days, len(recipes_list)))
    
    return selected_recipes

@app.route('/api/dinner-menu', methods=['GET'])
def get_dinner_menu():
    """Generate dinner menu using MongoDB recipes"""
    try:
        days = int(request.args.get('days', 5))
        
        # Fetch weather
        weather_data = get_weather_forecast(days)
        
        # Select recipes from MongoDB
        selected_recipes = select_dinner_recipes_mongo(weather_data, days)
        
        # Generate grocery list using MongoDB aggregation
        recipe_ids = [r['_id'] for r in selected_recipes]
        grocery_list = recipe_db.aggregate_ingredients(recipe_ids)
        
        return jsonify({
            "weather": weather_data,
            "recipes": convert_objectid_to_str(selected_recipes),
            "grocery_list": grocery_list
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error generating menu: {e}")
        return jsonify({"error": str(e)}), 500

# ============= Advanced MongoDB Features =============

@app.route('/api/recipes/search', methods=['POST'])
def search_recipes():
    """
    Search recipes with advanced filters
    
    Example body:
    {
      "ingredient": "chicken",
      "oven": true,
      "portions": {"$gte": 4},
      "tags": ["quick", "healthy"]
    }
    """
    try:
        filters = request.get_json()
        recipes = recipe_db.search_recipes(filters)
        return jsonify(convert_objectid_to_str(recipes)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ingredients', methods=['GET'])
def get_all_ingredients():
    """Get aggregated list of all ingredients with counts"""
    try:
        ingredients = recipe_db.aggregate_ingredients()
        return jsonify(ingredients), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recipes/by-ingredient/<ingredient>', methods=['GET'])
def recipes_by_ingredient(ingredient):
    """Find all recipes containing a specific ingredient"""
    try:
        recipes = recipe_db.search_by_ingredient(ingredient)
        return jsonify(convert_objectid_to_str(recipes)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= Migration Helper =============

@app.route('/api/migrate/check', methods=['GET'])
def check_migration_status():
    """Check MongoDB status and recipe count"""
    try:
        from db import get_db
        db = get_db()
        recipes_count = db.get_collection('recipes').count_documents({})
        
        return jsonify({
            "mongodb_connected": True,
            "recipes_count": recipes_count,
            "json_file_exists": os.path.exists("recipes.json")
        }), 200
    except Exception as e:
        return jsonify({
            "mongodb_connected": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
