"""
MongoDB database connection and utility functions
"""

import os
from pymongo import MongoClient
from datetime import datetime
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection"""
        # Try to get connection details from environment
        mongodb_uri = os.getenv('MONGODB_URI')
        mongo_password = os.getenv('MONGO_PASSWORD', 'changeme123')
        database_name = os.getenv('MONGODB_DATABASE', 'dinner_menu')
        
        # Build connection string if not provided
        if not mongodb_uri:
            encoded_password = quote_plus(mongo_password)
            # Try localhost first (for running on host), then fall back to Docker hostname
            localhost_uri = f'mongodb://admin:{encoded_password}@localhost:27017/'
            docker_uri = f'mongodb://admin:{encoded_password}@mongodb:27017/'
            
            try:
                # Try localhost first
                self.client = MongoClient(localhost_uri, serverSelectionTimeoutMS=2000)
                self.client.server_info()
                self.db = self.client[database_name]
                logger.info(f"Connected to MongoDB at localhost:27017")
                return
            except Exception:
                # Localhost failed, try Docker hostname
                try:
                    self.client = MongoClient(docker_uri, serverSelectionTimeoutMS=5000)
                    self.client.server_info()
                    self.db = self.client[database_name]
                    logger.info(f"Connected to MongoDB at mongodb:27017")
                    return
                except Exception as e:
                    logger.error(f"Failed to connect to MongoDB: {e}")
                    raise
        
        # Use provided MONGODB_URI
        try:
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client[database_name]
            logger.info(f"Connected to MongoDB: {database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_collection(self, collection_name):
        """Get a MongoDB collection"""
        return self.db[collection_name]
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Singleton instance
_mongodb_instance = None

def get_db():
    """Get MongoDB instance (singleton)"""
    global _mongodb_instance
    if _mongodb_instance is None:
        _mongodb_instance = MongoDB()
    return _mongodb_instance

# Recipe operations
class RecipeDB:
    """Recipe database operations"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.get_collection('recipes')
    
    def get_all_recipes(self):
        """Get all recipes"""
        return list(self.collection.find({}))
    
    def get_recipe_by_id(self, recipe_id):
        """Get recipe by ID"""
        from bson.objectid import ObjectId
        return self.collection.find_one({"_id": ObjectId(recipe_id)})
    
    def get_recipe_by_title(self, title):
        """Get recipe by title"""
        return self.collection.find_one({"title": title})
    
    def create_recipe(self, recipe_data):
        """Create new recipe"""
        recipe_data['created_at'] = datetime.utcnow()
        recipe_data['updated_at'] = datetime.utcnow()
        result = self.collection.insert_one(recipe_data)
        return str(result.inserted_id)
    
    def update_recipe(self, recipe_id, update_data):
        """Update existing recipe"""
        from bson.objectid import ObjectId
        update_data['updated_at'] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def delete_recipe(self, recipe_id):
        """Delete recipe"""
        from bson.objectid import ObjectId
        result = self.collection.delete_one({"_id": ObjectId(recipe_id)})
        return result.deleted_count > 0
    
    def search_recipes(self, filters=None):
        """Search recipes with filters"""
        query = filters or {}
        return list(self.collection.find(query))
    
    def aggregate_ingredients(self, recipe_ids=None):
        """
        Aggregate ingredients across recipes with summed quantities.
        Groups by (item, unit) and sums quantities, supporting fractions and decimals.
        Falls back to simple counting if quantities aren't parsed yet.
        """
        from ingredient_parser import quantity_to_float, normalize_unit
        
        match_stage = {}
        if recipe_ids:
            from bson.objectid import ObjectId
            match_stage = {"_id": {"$in": [ObjectId(rid) for rid in recipe_ids]}}
        
        pipeline = [
            {"$match": match_stage} if match_stage else {"$match": {}},
            {"$unwind": "$ingredients"},
            {"$group": {
                "_id": {
                    "item": {"$toLower": {"$ifNull": ["$ingredients.item", "$ingredients.original"]}},
                    "unit": {"$toLower": {"$ifNull": ["$ingredients.unit", ""]}}
                },
                "quantities": {"$push": {"$ifNull": ["$ingredients.quantity", ""]}},
                "recipes": {"$addToSet": "$title"}
            }},
            {"$sort": {"_id.item": 1}}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        # Post-process to sum quantities and filter out non-ingredients
        aggregated = []
        
        # Phrases to exclude from shopping lists
        exclude_phrases = [
            'look it up',
            'see recipe',
            'check recipe',
            'refer to',
            'as needed',
        ]
        
        for item in results:
            item_name = item['_id']['item']
            unit = normalize_unit(item['_id']['unit'])
            quantities = item['quantities']
            recipes = item['recipes']
            
            # Skip non-ingredient items
            if any(phrase in item_name.lower() for phrase in exclude_phrases):
                continue
            
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
                    ingredient_str = f"{qty_str} {unit} {item_name}"
                else:
                    ingredient_str = f"{qty_str} {item_name}"
            else:
                # No quantity found, just show the item
                if unit:
                    ingredient_str = f"{unit} {item_name}"
                else:
                    ingredient_str = item_name
            
            aggregated.append({
                "ingredient": ingredient_str,
                "item": item_name,
                "quantity": total if total > 0 else None,
                "unit": unit,
                "count": len(quantities),  # How many times it appears
                "recipes": recipes
            })
        
        return aggregated
    
    def get_recipes_by_cooking_method(self, oven=None, stove=None):
        """Filter recipes by cooking method"""
        query = {}
        if oven is not None:
            query["oven"] = oven
        if stove is not None:
            query["stove"] = stove
        return list(self.collection.find(query))
    
    def search_by_ingredient(self, ingredient_name):
        """Find recipes containing a specific ingredient"""
        return list(self.collection.find({
            "ingredients.item": {"$regex": ingredient_name, "$options": "i"}
        }))

def convert_objectid_to_str(obj):
    """Convert MongoDB ObjectId and datetime to string for JSON serialization"""
    from bson.objectid import ObjectId
    from datetime import datetime
    
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj
