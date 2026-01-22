import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'scripts', 'deprecated'))

# Mock streamlit before importing the app
sys.modules['streamlit'] = MagicMock()

class TestStreamlitHelpers(unittest.TestCase):
    """Test helper functions from streamlit_app.py"""
    
    @patch('requests.get')
    def test_get_recipes_success(self, mock_get):
        """Test successful recipe fetching"""
        # Import after mocking streamlit
        import streamlit_app
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'recipes': [
                {'title': 'Pasta', 'ingredients': ['pasta', 'sauce']}
            ]
        }
        mock_get.return_value = mock_response
        
        recipes = streamlit_app.get_recipes()
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0]['title'], 'Pasta')
    
    @patch('requests.get')
    def test_get_recipes_failure(self, mock_get):
        """Test recipe fetching with API failure"""
        import streamlit_app
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        recipes = streamlit_app.get_recipes()
        self.assertEqual(recipes, [])
    
    @patch('requests.get')
    def test_get_recipes_exception(self, mock_get):
        """Test recipe fetching with exception"""
        import streamlit_app
        
        mock_get.side_effect = Exception("Connection error")
        
        recipes = streamlit_app.get_recipes()
        self.assertEqual(recipes, [])
    
    @patch('requests.post')
    def test_add_recipe_success(self, mock_post):
        """Test successful recipe addition"""
        import streamlit_app
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'message': 'Recipe added'
        }
        mock_post.return_value = mock_response
        
        recipe_data = {'title': 'New Recipe', 'ingredients': ['ing1']}
        result = streamlit_app.add_recipe_api(recipe_data)
        
        self.assertTrue(result['success'])
    
    @patch('requests.post')
    def test_add_recipe_exception(self, mock_post):
        """Test recipe addition with exception"""
        import streamlit_app
        
        mock_post.side_effect = Exception("Network error")
        
        recipe_data = {'title': 'New Recipe', 'ingredients': ['ing1']}
        result = streamlit_app.add_recipe_api(recipe_data)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('requests.delete')
    def test_delete_recipe_success(self, mock_delete):
        """Test successful recipe deletion"""
        import streamlit_app
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'message': 'Recipe deleted'
        }
        mock_delete.return_value = mock_response
        
        result = streamlit_app.delete_recipe_api(0)
        self.assertTrue(result['success'])
    
    @patch('requests.get')
    def test_get_weather_success(self, mock_get):
        """Test successful weather fetching"""
        import streamlit_app
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'weather': {
                'location': 'Spokane, WA',
                'forecast': [{'day': 'Monday', 'temp': 75.0}]
            }
        }
        mock_get.return_value = mock_response
        
        result = streamlit_app.get_weather(7)
        self.assertTrue(result['success'])
        self.assertIn('weather', result)
    
    @patch('requests.get')
    def test_get_dinner_menu_success(self, mock_get):
        """Test successful dinner menu fetching"""
        import streamlit_app
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'weather': {'location': 'Spokane, WA'},
            'dinner_plan': {
                'selected_recipes': [],
                'total_portions': 0,
                'grocery_list': []
            }
        }
        mock_get.return_value = mock_response
        
        result = streamlit_app.get_dinner_menu(7)
        self.assertTrue(result['success'])
        self.assertIn('dinner_plan', result)
    
    @patch('requests.get')
    def test_get_quick_dinner_menu_success(self, mock_get):
        """Test successful quick dinner menu fetching"""
        import streamlit_app
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'dinner_plan': {
                'selected_recipes': [
                    {'title': 'Pasta', 'ingredients': ['pasta'], 'portions': '2'}
                ],
                'total_portions': 2,
                'grocery_list': [{'ingredient': 'pasta', 'count': 1}]
            }
        }
        mock_get.return_value = mock_response
        
        result = streamlit_app.get_quick_dinner_menu(7)
        self.assertTrue(result['success'])
        self.assertIn('dinner_plan', result)
        self.assertIn('grocery_list', result['dinner_plan'])
    
    @patch('requests.post')
    def test_reroll_dinner_menu_success(self, mock_post):
        """Test successful dinner menu re-roll with cached weather"""
        import streamlit_app
        
        cached_weather = {
            'location': 'Spokane, WA',
            'forecast': [
                {'day': 'Monday', 'date': '2026-01-20', 'temp': 75.0},
                {'day': 'Tuesday', 'date': '2026-01-21', 'temp': 80.0}
            ]
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'weather': cached_weather,
            'dinner_plan': {
                'selected_recipes': [
                    {'title': 'Salad', 'ingredients': ['lettuce'], 'portions': '2'}
                ],
                'total_portions': 2,
                'grocery_list': [{'ingredient': 'lettuce', 'count': 1}]
            }
        }
        mock_post.return_value = mock_response
        
        result = streamlit_app.reroll_dinner_menu(2, cached_weather)
        self.assertTrue(result['success'])
        self.assertIn('dinner_plan', result)
        self.assertEqual(result['weather'], cached_weather)
    
    @patch('requests.post')
    def test_reroll_single_recipe(self, mock_post):
        """Test re-rolling a single recipe with keep_indices"""
        import streamlit_app
        
        cached_weather = {'location': 'Spokane, WA', 'forecast': []}
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'weather': cached_weather,
            'dinner_plan': {
                'selected_recipes': [
                    {'title': 'Kept Recipe', 'ingredients': ['a'], 'portions': '2'},
                    {'title': 'New Recipe', 'ingredients': ['b'], 'portions': '2'}
                ],
                'total_portions': 4,
                'grocery_list': []
            }
        }
        mock_post.return_value = mock_response
        
        # Re-roll with keep_indices
        result = streamlit_app.reroll_dinner_menu(2, cached_weather, keep_indices=[0, 2])
        self.assertTrue(result['success'])
        # Verify the request was made with exclude_indices
        call_args = mock_post.call_args
        self.assertIn('exclude_indices', call_args[1]['json'])
    
    @patch('requests.post')
    def test_reroll_dinner_menu_failure(self, mock_post):
        """Test dinner menu re-roll failure"""
        import streamlit_app
        
        cached_weather = {'location': 'Spokane, WA', 'forecast': []}
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': False,
            'error': 'Failed to generate menu'
        }
        mock_post.return_value = mock_response
        
        result = streamlit_app.reroll_dinner_menu(2, cached_weather)
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('requests.post')
    def test_reroll_dinner_menu_exception(self, mock_post):
        """Test dinner menu re-roll with exception"""
        import streamlit_app
        
        mock_post.side_effect = Exception("Network error")
        cached_weather = {'location': 'Spokane, WA', 'forecast': []}
        
        result = streamlit_app.reroll_dinner_menu(2, cached_weather)
        self.assertFalse(result['success'])
        self.assertIn('error', result)

if __name__ == '__main__':
    unittest.main()

