import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

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

if __name__ == '__main__':
    unittest.main()
