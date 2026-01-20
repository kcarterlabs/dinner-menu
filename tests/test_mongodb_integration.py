"""
Integration tests for MongoDB connection and recipe storage
"""
import unittest
import os
import sys
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


class TestMongoDBConnection(unittest.TestCase):
    """Test MongoDB connection and authentication"""
    
    def test_mongodb_connection(self):
        """Test that MongoDB connection is successful"""
        from db import MongoDB
        
        try:
            mongo = MongoDB()
            self.assertIsNotNone(mongo.db, "MongoDB database should be connected")
            self.assertIsNotNone(mongo.client, "MongoDB client should exist")
            
            # Test that we can ping the server
            mongo.client.server_info()
            mongo.close()
        except Exception as e:
            self.fail(f"MongoDB connection failed: {e}")
    
    def test_mongodb_authentication(self):
        """Test that MongoDB authentication works with special characters in password"""
        from db import MongoDB
        
        mongo_password = os.getenv('MONGO_PASSWORD')
        self.assertIsNotNone(mongo_password, "MONGO_PASSWORD should be set in environment")
        
        # Test connection with the actual password
        try:
            mongo = MongoDB()
            self.assertTrue(mongo.db is not None, "Should successfully authenticate with special characters in password")
            mongo.close()
        except Exception as e:
            self.fail(f"Authentication failed with special characters: {e}")
    
    def test_mongodb_database_exists(self):
        """Test that the dinner_menu database exists"""
        from db import MongoDB
        
        mongo = MongoDB()
        self.assertEqual(mongo.db.name, 'dinner_menu', "Should connect to dinner_menu database")
        mongo.close()


class TestRecipeDB(unittest.TestCase):
    """Test RecipeDB operations"""
    
    def setUp(self):
        """Set up test database connection"""
        from db import RecipeDB
        self.recipe_db = RecipeDB()
    
    def tearDown(self):
        """Clean up test data"""
        # Note: We don't delete test data to avoid affecting production
        pass
    
    def test_create_recipe_with_structured_ingredients(self):
        """Test creating a recipe with structured ingredient format"""
        test_recipe = {
            "title": f"Test Recipe {datetime.now().timestamp()}",
            "date": "2026-01-20",
            "ingredients": [
                {
                    "quantity": "1",
                    "unit": "cup",
                    "item": "test ingredient",
                    "original": "1 cup test ingredient"
                },
                {
                    "quantity": "2",
                    "unit": "tsp",
                    "item": "test spice",
                    "original": "2 tsp test spice"
                }
            ],
            "oven": False,
            "stove": True,
            "portions": "4"
        }
        
        # Create recipe
        recipe_id = self.recipe_db.create_recipe(test_recipe)
        self.assertIsNotNone(recipe_id, "Recipe should be created and return an ID")
        
        # Verify it was saved
        saved_recipe = self.recipe_db.get_recipe_by_id(recipe_id)
        self.assertIsNotNone(saved_recipe, "Recipe should be retrievable by ID")
        self.assertEqual(saved_recipe['title'], test_recipe['title'])
        
        # Verify structured ingredients are preserved
        self.assertEqual(len(saved_recipe['ingredients']), 2)
        self.assertEqual(saved_recipe['ingredients'][0]['quantity'], "1")
        self.assertEqual(saved_recipe['ingredients'][0]['unit'], "cup")
        self.assertEqual(saved_recipe['ingredients'][0]['item'], "test ingredient")
        
        # Clean up
        self.recipe_db.delete_recipe(recipe_id)
    
    def test_get_all_recipes(self):
        """Test retrieving all recipes from MongoDB"""
        recipes = self.recipe_db.get_all_recipes()
        self.assertIsInstance(recipes, list, "Should return a list of recipes")
        self.assertGreater(len(recipes), 0, "Should have at least one recipe")
        
        # Verify recipe structure
        first_recipe = recipes[0]
        self.assertIn('title', first_recipe)
        self.assertIn('ingredients', first_recipe)
    
    def test_aggregate_ingredients(self):
        """Test ingredient aggregation with structured format"""
        from db import aggregate_ingredients
        
        aggregated = aggregate_ingredients()
        self.assertIsInstance(aggregated, list, "Should return a list of aggregated ingredients")
        
        # If there are aggregated ingredients, verify format
        if len(aggregated) > 0:
            # Should be formatted as strings like "1.5 cup flour"
            self.assertIsInstance(aggregated[0], str, "Aggregated ingredients should be strings")


class TestAPIMongoDBIntegration(unittest.TestCase):
    """Test API endpoints save to MongoDB"""
    
    def setUp(self):
        """Set up test client"""
        import app
        self.app = app.app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    def test_add_recipe_saves_to_mongodb(self):
        """Test that POST /api/recipes saves to MongoDB"""
        from db import RecipeDB
        
        recipe_db = RecipeDB()
        initial_count = recipe_db.db.recipes.count_documents({})
        
        # Add a test recipe via API
        test_recipe = {
            "title": f"API Test Recipe {datetime.now().timestamp()}",
            "date": "2026-01-20",
            "ingredients": [
                {
                    "quantity": "1",
                    "unit": "cup",
                    "item": "api test ingredient",
                    "original": "1 cup api test ingredient"
                }
            ],
            "oven": True,
            "stove": False,
            "portions": "2"
        }
        
        response = self.client.post('/api/recipes', 
                                    json=test_recipe,
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 201, "Should successfully create recipe")
        
        # Verify it was saved to MongoDB
        new_count = recipe_db.db.recipes.count_documents({})
        self.assertEqual(new_count, initial_count + 1, "Recipe should be saved to MongoDB")
        
        # Clean up - find and delete the test recipe
        test_recipe_in_db = recipe_db.db.recipes.find_one({"title": test_recipe["title"]})
        if test_recipe_in_db:
            recipe_db.delete_recipe(str(test_recipe_in_db['_id']))
    
    def test_add_recipe_with_string_ingredients(self):
        """Test that legacy string ingredients are converted to structured format"""
        from db import RecipeDB
        
        recipe_db = RecipeDB()
        
        # Add a recipe with string ingredients (legacy format)
        test_recipe = {
            "title": f"Legacy Format Test {datetime.now().timestamp()}",
            "date": "2026-01-20",
            "ingredients": [
                "1 cup flour",
                "2 tsp sugar"
            ],
            "oven": True,
            "stove": False,
            "portions": "4"
        }
        
        response = self.client.post('/api/recipes',
                                    json=test_recipe,
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 201, "Should accept legacy format")
        
        # Verify it was converted to structured format in MongoDB
        response_data = response.get_json()
        saved_recipe_id = response_data['recipe'].get('_id')
        
        if saved_recipe_id:
            saved_recipe = recipe_db.get_recipe_by_id(saved_recipe_id)
            self.assertIsInstance(saved_recipe['ingredients'][0], dict, "Should convert to structured format")
            self.assertIn('item', saved_recipe['ingredients'][0])
            
            # Clean up
            recipe_db.delete_recipe(saved_recipe_id)
    
    def test_use_mongodb_flag(self):
        """Test that USE_MONGODB flag is True when MongoDB is available"""
        import app
        
        self.assertTrue(app.USE_MONGODB, "USE_MONGODB should be True when MongoDB is connected")
        self.assertIsNotNone(app.recipe_db, "recipe_db should be initialized")


if __name__ == '__main__':
    unittest.main()
