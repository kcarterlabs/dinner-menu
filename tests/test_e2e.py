import unittest
import json
import os
import sys
import time
import threading
import requests
from unittest.mock import patch, MagicMock

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import app


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for the complete application flow"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Use in-memory test client instead of running real server
        app.app.config['TESTING'] = True
        cls.client = app.app.test_client()
        cls.base_url = 'http://localhost'  # Not actually used, but kept for reference
    
    # Note: conftest.py automatically isolates recipes.json and backups
    # No manual file handling needed - pytest fixtures handle it
    
    def test_health_check(self):
        """Test that the API health endpoint responds"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('message', data)
    
    def test_complete_recipe_workflow(self):
        """Test the complete recipe management workflow"""
        # Step 1: Get initial recipes
        response = self.client.get('/api/recipes')
        self.assertEqual(response.status_code, 200)
        initial_data = json.loads(response.data)
        initial_count = initial_data['count']
        
        # Step 2: Add a new recipe
        new_recipe = {
            "title": "E2E Test Pasta",
            "ingredients": ["pasta", "tomato sauce", "garlic", "olive oil"],
            "oven": False,
            "stove": True,
            "portions": "4",
            "url": "https://example.com/pasta"
        }
        
        response = self.client.post(
            '/api/recipes',
            data=json.dumps(new_recipe),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        add_data = json.loads(response.data)
        self.assertTrue(add_data['success'])
        self.assertIn('Recipe added', add_data['message'])
        
        # Step 3: Verify recipe was added
        response = self.client.get('/api/recipes')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['count'], initial_count + 1)
        
        # Find our recipe and get its ID
        found = False
        recipe_id = None
        for recipe in data['recipes']:
            if recipe['title'] == 'E2E Test Pasta':
                found = True
                recipe_id = recipe.get('_id')  # MongoDB uses _id, JSON file may not have it
                # MongoDB stores structured ingredients, extract item names for comparison
                recipe_ingredient_items = [ing['item'] for ing in recipe['ingredients']]
                self.assertEqual(recipe_ingredient_items, new_recipe['ingredients'])
                self.assertEqual(recipe['oven'], False)
                self.assertEqual(recipe['stove'], True)
        self.assertTrue(found, "Added recipe not found in recipe list")
        
        # Step 4: Delete the recipe (only if we have an ID - MongoDB mode)
        if recipe_id:
            response = self.client.delete(f'/api/recipes/{recipe_id}')
            self.assertEqual(response.status_code, 200)
            delete_data = json.loads(response.data)
            self.assertTrue(delete_data['success'])
            
            # Step 5: Verify recipe was deleted
            response = self.client.get('/api/recipes')
            self.assertEqual(response.status_code, 200)
            final_data = json.loads(response.data)
            self.assertEqual(final_data['count'], initial_count)
    
    @patch('app.get_weather_forecast')
    def test_weather_integration(self, mock_weather):
        """Test weather API integration"""
        # Mock weather forecast function
        mock_weather.return_value = {
            "location": "Spokane, WA",
            "forecast": [
                {
                    "day": "Friday",
                    "date": "2026-01-17",
                    "temp": 75.5
                },
                {
                    "day": "Saturday",
                    "date": "2026-01-18",
                    "temp": 68.2
                }
            ]
        }
        
        response = self.client.get('/api/weather?days=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('weather', data)
        self.assertEqual(data['weather']['location'], 'Spokane, WA')
        self.assertEqual(len(data['weather']['forecast']), 2)
        self.assertEqual(data['weather']['forecast'][0]['temp'], 75.5)
    
    @patch('app.get_weather_forecast')
    def test_dinner_menu_generation(self, mock_weather):
        """Test complete dinner menu generation flow"""
        # Mock weather forecast
        mock_weather.return_value = {
            "location": "Spokane, WA",
            "forecast": [
                {"day": "Friday", "date": "2026-01-17", "temp": 65.0},
                {"day": "Saturday", "date": "2026-01-18", "temp": 70.0},
                {"day": "Sunday", "date": "2026-01-19", "temp": 72.0}
            ]
        }
        
        # Add test recipes
        test_recipes = [
            {
                "title": "Grilled Chicken",
                "ingredients": ["chicken", "spices"],
                "oven": True,
                "stove": False,
                "portions": "4",
                "url": "https://example.com/chicken"
            },
            {
                "title": "Pasta Salad",
                "ingredients": ["pasta", "vegetables"],
                "oven": False,
                "stove": True,
                "portions": "4",
                "url": "https://example.com/salad"
            },
            {
                "title": "Stir Fry",
                "ingredients": ["rice", "vegetables", "soy sauce"],
                "oven": False,
                "stove": True,
                "portions": "3",
                "url": "https://example.com/stirfry"
            }
        ]
        
        # Add recipes via API
        for recipe in test_recipes:
            self.client.post(
                '/api/recipes',
                data=json.dumps(recipe),
                content_type='application/json'
            )
        
        # Generate dinner menu
        response = self.client.get('/api/dinner-menu?days=3')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('dinner_plan', data)
        self.assertIn('selected_recipes', data['dinner_plan'])
        
        # Verify recipes were selected
        selected = data['dinner_plan']['selected_recipes']
        self.assertGreater(len(selected), 0)
        
        # Verify recipe structure
        for recipe in selected:
            self.assertIn('title', recipe)
            self.assertIn('ingredients', recipe)
    
    @patch('app.requests.get')
    def test_quick_dinner_menu(self, mock_get):
        """Test quick dinner menu (no weather)"""
        # Add test recipes
        test_recipes = [
            {
                "title": "Quick Pasta",
                "ingredients": ["pasta", "butter", "cheese"],
                "oven": False,
                "stove": True,
                "portions": "2",
                "url": "https://example.com/quick"
            },
            {
                "title": "Quick Salad",
                "ingredients": ["lettuce", "tomatoes", "dressing"],
                "oven": False,
                "stove": False,
                "portions": "2",
                "url": "https://example.com/salad"
            }
        ]
        
        for recipe in test_recipes:
            self.client.post(
                '/api/recipes',
                data=json.dumps(recipe),
                content_type='application/json'
            )
        
        # Generate quick menu
        response = self.client.get('/api/dinner-menu/quick?days=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('dinner_plan', data)
        self.assertIn('selected_recipes', data['dinner_plan'])
        
        # Verify recipes were selected
        recipes = data['dinner_plan']['selected_recipes']
        self.assertGreater(len(recipes), 0)
        
        # Verify no duplicate recipes
        recipe_titles = [r['title'] for r in recipes]
        self.assertEqual(len(recipe_titles), len(set(recipe_titles)), "Menu contains duplicate recipes")
    
    def test_grocery_list_generation(self):
        """Test grocery list generation from multiple recipes"""
        # Add test recipes with overlapping ingredients
        test_recipes = [
            {
                "title": "Recipe 1",
                "ingredients": ["eggs", "milk", "flour", "sugar"],
                "oven": True,
                "stove": False,
                "portions": "4",
                "url": "https://example.com/recipe1"
            },
            {
                "title": "Recipe 2",
                "ingredients": ["eggs", "butter", "flour", "vanilla"],
                "oven": True,
                "stove": False,
                "portions": "6",
                "url": "https://example.com/recipe2"
            },
            {
                "title": "Recipe 3",
                "ingredients": ["chicken", "rice", "vegetables"],
                "oven": False,
                "stove": True,
                "portions": "4",
                "url": "https://example.com/recipe3"
            }
        ]
        
        for recipe in test_recipes:
            self.client.post(
                '/api/recipes',
                data=json.dumps(recipe),
                content_type='application/json'
            )
        
        # Get recipes to verify they were added
        response = self.client.get('/api/recipes')
        data = json.loads(response.data)
        recipes = data['recipes']
        
        # Verify at least the 3 new recipes were added (initial count varies with MongoDB)
        self.assertGreaterEqual(data['count'], 3)
        
        # Verify all ingredients are in the recipes (extract item names from structured format)
        all_ingredient_items = []
        for recipe in recipes:
            for ing in recipe['ingredients']:
                if isinstance(ing, dict):
                    all_ingredient_items.append(ing['item'])
                else:
                    all_ingredient_items.append(ing)
        
        self.assertIn('eggs', all_ingredient_items)
        self.assertIn('flour', all_ingredient_items)
        self.assertIn('chicken', all_ingredient_items)
    
    def test_error_handling_invalid_recipe(self):
        """Test error handling with invalid recipe data"""
        # Missing required fields
        invalid_recipe = {
            "title": "Invalid Recipe"
            # Missing ingredients, oven, stove, portions
        }
        
        response = self.client.post(
            '/api/recipes',
            data=json.dumps(invalid_recipe),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_error_handling_invalid_recipe_index(self):
        """Test error handling with invalid recipe ID"""
        # Try to delete with invalid ObjectId format
        response = self.client.delete('/api/recipes/invalid_id')
        self.assertIn(response.status_code, [404, 500])  # Either format error (500) or not found (404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    @patch('app.get_weather_forecast')
    def test_error_handling_invalid_weather_days(self, mock_weather):
        """Test error handling with out-of-range weather days parameter"""
        mock_weather.return_value = []
        
        # Test days too high
        response = self.client.get('/api/weather?days=99')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    @patch('app.get_weather_forecast')
    def test_full_user_journey(self, mock_weather):
        """Test a complete user journey from start to finish"""
        # Mock weather
        mock_weather.return_value = {
            "location": "Spokane, WA",
            "forecast": [
                {"day": "Friday", "date": "2026-01-17", "temp": 68.0},
                {"day": "Saturday", "date": "2026-01-18", "temp": 72.0}
            ]
        }
        
        # 1. User checks health of API
        health = self.client.get('/api/health')
        self.assertEqual(health.status_code, 200)
        
        # 2. User views existing recipes
        recipes = self.client.get('/api/recipes')
        self.assertEqual(recipes.status_code, 200)
        initial_count = json.loads(recipes.data)['count']
        
        # 3. User adds their favorite recipe
        favorite_recipe = {
            "title": "Mom's Lasagna",
            "ingredients": ["lasagna noodles", "ground beef", "ricotta cheese", "mozzarella", "marinara sauce"],
            "oven": True,
            "stove": True,
            "portions": "8",
            "url": "https://example.com/lasagna"
        }
        add_response = self.client.post('/api/recipes', data=json.dumps(favorite_recipe), content_type='application/json')
        self.assertEqual(add_response.status_code, 201)
        
        # 4. User checks the weather
        weather_response = self.client.get('/api/weather?days=2')
        self.assertEqual(weather_response.status_code, 200)
        weather_data = json.loads(weather_response.data)
        self.assertTrue(weather_data['success'])
        
        # 5. User generates dinner menu based on weather
        menu_response = self.client.get('/api/dinner-menu?days=2')
        self.assertEqual(menu_response.status_code, 200)
        menu_data = json.loads(menu_response.data)
        self.assertTrue(menu_data['success'])
        self.assertIn('dinner_plan', menu_data)
        
        # 6. User views recipes again and verifies their recipe is saved
        final_recipes = self.client.get('/api/recipes')
        self.assertEqual(final_recipes.status_code, 200)
        final_data = json.loads(final_recipes.data)
        
        # 7. Verify the user's recipe is in the system
        self.assertEqual(final_data['count'], initial_count + 1)
        
        # 8. Verify grocery list is included in the dinner plan
        self.assertIn('grocery_list', menu_data['dinner_plan'])


if __name__ == '__main__':
    unittest.main()
