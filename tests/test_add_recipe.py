import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import sys
import os
from io import StringIO

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the module - using importlib to handle the hyphen in filename
import importlib.util
spec = importlib.util.spec_from_file_location("add_recipe", os.path.join(parent_dir, "add-recipe.py"))
add_recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(add_recipe)

class TestAddRecipe(unittest.TestCase):
    
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='[{"title": "Pasta", "ingredients": ["pasta"]}]')
    def test_load_recipes_success(self, mock_file, mock_exists):
        """Test successfully loading recipes"""
        recipes = add_recipe.load_recipes()
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0]['title'], 'Pasta')
    
    @patch('os.path.exists', return_value=False)
    def test_load_recipes_file_not_exists(self, mock_exists):
        """Test loading recipes when file doesn't exist"""
        recipes = add_recipe.load_recipes()
        self.assertEqual(recipes, [])
    
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_recipes_corrupted_json(self, mock_file, mock_exists):
        """Test loading recipes with corrupted JSON"""
        with patch('builtins.print'):
            recipes = add_recipe.load_recipes()
            self.assertEqual(recipes, [])
    
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('shutil.copy')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_recipes_with_backup(self, mock_file, mock_copy, mock_makedirs, mock_exists):
        """Test saving recipes creates backup"""
        recipes = [{"title": "Test", "ingredients": []}]
        
        with patch('builtins.print'):
            add_recipe.save_recipes(recipes)
        
        mock_makedirs.assert_called_once()
        mock_copy.assert_called_once()
    
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    def test_save_recipes_no_backup_when_file_missing(self, mock_file, mock_exists):
        """Test saving recipes without backup when file doesn't exist"""
        recipes = [{"title": "Test", "ingredients": []}]
        
        with patch('builtins.print'):
            add_recipe.save_recipes(recipes)
        
        # Should still write the file
        mock_file.assert_called()
    
    @patch('builtins.input', side_effect=['Test Recipe', '2026-01-20', 'pasta, sauce', 'y', 'n', '4'])
    def test_add_recipe_user_input(self, mock_input):
        """Test adding recipe with user input"""
        recipes = []
        
        with patch('builtins.print'):
            result = add_recipe.add_recipe(recipes)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Test Recipe')
        self.assertEqual(result[0]['date'], '2026-01-20')
        self.assertEqual(len(result[0]['ingredients']), 2)
        self.assertTrue(result[0]['oven'])
        self.assertFalse(result[0]['stove'])
        self.assertEqual(result[0]['portions'], '4')
    
    @patch('builtins.input', side_effect=['Pizza', '2026-01-20', 'dough,cheese,sauce', 'n', 'y', '2'])
    def test_add_recipe_no_oven_yes_stove(self, mock_input):
        """Test adding recipe with stove but no oven"""
        recipes = []
        
        with patch('builtins.print'):
            result = add_recipe.add_recipe(recipes)
        
        self.assertEqual(result[0]['title'], 'Pizza')
        self.assertFalse(result[0]['oven'])
        self.assertTrue(result[0]['stove'])
    
    @patch('builtins.input', side_effect=['Salad', '2026-01-20', '  lettuce  , tomato,  cucumber ', 'n', 'n', '1'])
    def test_add_recipe_strips_whitespace(self, mock_input):
        """Test that ingredient whitespace is stripped"""
        recipes = []
        
        with patch('builtins.print'):
            result = add_recipe.add_recipe(recipes)
        
        # Should strip whitespace from ingredients
        self.assertIn('lettuce', result[0]['ingredients'])
        self.assertIn('tomato', result[0]['ingredients'])
        self.assertIn('cucumber', result[0]['ingredients'])
        # Should not have empty strings
        self.assertNotIn('', result[0]['ingredients'])

if __name__ == '__main__':
    unittest.main()
