import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import app

class TestFlaskAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    @patch('app.load_recipes')
    def test_get_recipes(self, mock_load):
        """Test getting all recipes"""
        mock_load.return_value = [
            {"title": "Pasta", "ingredients": ["pasta", "sauce"], "oven": False, "stove": True, "portions": "2"}
        ]
        
        response = self.client.get('/api/recipes')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['recipes']), 1)
    
    @patch('app.save_recipes')
    @patch('app.load_recipes')
    def test_add_recipe(self, mock_load, mock_save):
        """Test adding a new recipe"""
        mock_load.return_value = []
        
        new_recipe = {
            "title": "Test Recipe",
            "ingredients": ["ingredient1", "ingredient2"],
            "oven": True,
            "stove": False,
            "portions": "4"
        }
        
        response = self.client.post('/api/recipes', 
                                   data=json.dumps(new_recipe),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['recipe']['title'], 'Test Recipe')
        mock_save.assert_called_once()
    
    def test_add_recipe_missing_field(self):
        """Test adding recipe with missing required field"""
        incomplete_recipe = {
            "ingredients": ["ingredient1"]
            # Missing 'title'
        }
        
        response = self.client.post('/api/recipes',
                                   data=json.dumps(incomplete_recipe),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    @patch('app.save_recipes')
    @patch('app.load_recipes')
    def test_delete_recipe(self, mock_load, mock_save):
        """Test deleting a recipe"""
        mock_load.return_value = [
            {"title": "Recipe 1", "ingredients": [], "oven": False, "stove": False, "portions": "1"},
            {"title": "Recipe 2", "ingredients": [], "oven": False, "stove": False, "portions": "1"}
        ]
        
        response = self.client.delete('/api/recipes/0')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted_recipe']['title'], 'Recipe 1')
        mock_save.assert_called_once()
    
    @patch('app.load_recipes')
    def test_delete_recipe_invalid_index(self, mock_load):
        """Test deleting recipe with invalid index"""
        mock_load.return_value = [
            {"title": "Recipe 1", "ingredients": [], "oven": False, "stove": False, "portions": "1"}
        ]
        
        response = self.client.delete('/api/recipes/5')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    @patch('app.get_weather_forecast')
    def test_get_weather(self, mock_weather):
        """Test weather endpoint"""
        mock_weather.return_value = {
            "location": "Spokane, WA",
            "forecast": [
                {"day": "Monday", "date": "2026-01-20", "temp": 75.0}
            ]
        }
        
        response = self.client.get('/api/weather?days=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('weather', data)
    
    def test_get_weather_invalid_days(self):
        """Test weather endpoint with invalid days parameter"""
        response = self.client.get('/api/weather?days=20')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    @patch('app.select_dinner_recipes')
    @patch('app.get_weather_forecast')
    def test_dinner_menu(self, mock_weather, mock_select):
        """Test dinner menu endpoint"""
        mock_weather.return_value = {
            "location": "Spokane, WA",
            "forecast": [{"day": "Monday", "date": "2026-01-20", "temp": 75.0}]
        }
        mock_select.return_value = {
            "selected_recipes": [
                {"title": "Pasta", "ingredients": ["pasta"], "oven": False, "stove": True, "portions": "2"}
            ],
            "total_portions": 2,
            "days_requested": 1,
            "too_hot_for_oven": False,
            "grocery_list": [{"ingredient": "pasta", "count": 1}]
        }
        
        response = self.client.get('/api/dinner-menu?days=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('dinner_plan', data)
    
    @patch('app.select_dinner_recipes')
    def test_dinner_menu_reroll_with_cached_weather(self, mock_select):
        """Test re-rolling dinner menu with cached weather data"""
        cached_weather = {
            "location": "Spokane, WA",
            "forecast": [
                {"day": "Monday", "date": "2026-01-20", "temp": 75.0},
                {"day": "Tuesday", "date": "2026-01-21", "temp": 80.0}
            ]
        }
        mock_select.return_value = {
            "selected_recipes": [
                {"title": "Salad", "ingredients": ["lettuce"], "oven": False, "stove": False, "portions": "2"}
            ],
            "total_portions": 2,
            "days_requested": 2,
            "too_hot_for_oven": False,
            "grocery_list": [{"ingredient": "lettuce", "count": 1}]
        }
        
        response = self.client.post(
            '/api/dinner-menu?days=2',
            data=json.dumps({"weather": cached_weather}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['weather'], cached_weather)
        self.assertIn('dinner_plan', data)
        # When no reroll_index is provided, it should pass None and []
        mock_select.assert_called_once_with(cached_weather, 2, None, [])
    
    @patch('app.select_dinner_recipes')
    def test_dinner_menu_reroll_single_recipe(self, mock_select):
        """Test re-rolling a single recipe while keeping others"""
        cached_weather = {
            "location": "Spokane, WA",
            "forecast": [{"day": "Monday", "date": "2026-01-20", "temp": 75.0}]
        }
        current_menu = [
            {"title": "Recipe 1", "ingredients": ["a"], "oven": False, "stove": True, "portions": "2"},
            {"title": "Recipe 2", "ingredients": ["b"], "oven": False, "stove": True, "portions": "2"},
            {"title": "Recipe 3", "ingredients": ["c"], "oven": False, "stove": True, "portions": "2"}
        ]
        mock_select.return_value = {
            "selected_recipes": [
                {"title": "Recipe 1", "ingredients": ["a"], "oven": False, "stove": True, "portions": "2"},
                {"title": "New Recipe", "ingredients": ["new"], "oven": False, "stove": True, "portions": "2"},
                {"title": "Recipe 3", "ingredients": ["c"], "oven": False, "stove": True, "portions": "2"}
            ],
            "total_portions": 6,
            "days_requested": 2,
            "too_hot_for_oven": False,
            "grocery_list": [{"ingredient": "a", "count": 1}, {"ingredient": "new", "count": 1}, {"ingredient": "c", "count": 1}]
        }
        
        # Re-roll with reroll_index to replace recipe at index 1
        response = self.client.post(
            '/api/dinner-menu?days=2',
            data=json.dumps({
                "weather": cached_weather,
                "reroll_index": 1,
                "current_menu": current_menu
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        # Verify reroll_index and current_menu was passed to select function
        mock_select.assert_called_once_with(cached_weather, 2, 1, current_menu)
    
    def test_dinner_menu_reroll_missing_weather(self):
        """Test re-rolling without weather data returns error"""
        response = self.client.post(
            '/api/dinner-menu?days=2',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Weather data required', data['error'])
    
    @patch('app.load_recipes')
    def test_quick_dinner_menu(self, mock_load):
        """Test quick dinner menu endpoint"""
        mock_load.return_value = [
            {"title": "Recipe 1", "ingredients": ["ing1"], "oven": False, "stove": True, "portions": "3"}
        ]
        
        response = self.client.get('/api/dinner-menu/quick?days=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('dinner_plan', data)
        self.assertIn('grocery_list', data['dinner_plan'])
    
    def test_generate_grocery_list(self):
        """Test grocery list generation"""
        recipes = [
            {"title": "Recipe 1", "ingredients": ["pasta", "sauce"], "portions": "2"},
            {"title": "Recipe 2", "ingredients": ["pasta", "cheese"], "portions": "2"}
        ]
        
        grocery_list = app.generate_grocery_list(recipes)
        
        # Should have 3 unique ingredients
        self.assertEqual(len(grocery_list), 3)
        
        # Pasta should appear twice
        pasta_item = next(item for item in grocery_list if item['ingredient'] == 'pasta')
        self.assertEqual(pasta_item['count'], 2)
    
    def test_load_recipes_file_not_exists(self):
        """Test loading recipes when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            recipes = app.load_recipes()
            self.assertEqual(recipes, [])
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('os.path.exists', return_value=True)
    def test_load_recipes_invalid_json(self, mock_exists, mock_file):
        """Test loading recipes with invalid JSON"""
        recipes = app.load_recipes()
        self.assertEqual(recipes, [])

if __name__ == '__main__':
    unittest.main()
