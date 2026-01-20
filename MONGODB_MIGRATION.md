# MongoDB Migration Guide

## Overview
Migrate from `recipes.json` to MongoDB for better database management, queries, and scalability.

## Benefits
- **Better Queries**: Complex filtering (by ingredients, cooking method, portions, etc.)
- **Aggregation**: Powerful ingredient counting and statistics
- **Scalability**: Handle thousands of recipes easily
- **Relationships**: Link recipes to tags, categories, meal plans
- **Indexing**: Fast searches on titles, ingredients, tags

## MongoDB Schema Design

```javascript
// recipes collection
{
  _id: ObjectId("..."),
  title: "Hearty Dutch Oven Beef Stew",
  date: ISODate("2025-06-15"),
  ingredients: [
    {
      item: "yellow onion",
      quantity: "1 medium",
      unit: "whole",
      original: "1 medium yellow onion, diced"
    },
    {
      item: "garlic",
      quantity: "5",
      unit: "cloves",
      original: "5 cloves garlic, minced"
    }
  ],
  oven: true,
  stove: true,
  portions: 3,
  tags: ["beef", "stew", "comfort-food"],
  cookTime: 120, // minutes
  difficulty: "medium",
  created_at: ISODate("2025-01-01"),
  updated_at: ISODate("2025-01-15")
}
```

## Migration Steps

### 1. Install Dependencies
```bash
pip install pymongo python-dotenv
```

### 2. Set Up MongoDB
**Option A: MongoDB Atlas (Cloud - Free Tier)**
- Sign up at https://www.mongodb.com/cloud/atlas
- Create cluster → Get connection string
- Add to `.env`: `MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/dinner_menu`

**Option B: Local MongoDB (Docker)**
```bash
docker run -d -p 27017:27017 --name dinner-menu-mongo \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:7
```

### 3. Migration Script (migrate_to_mongo.py)
See: `migrate_to_mongo.py`

### 4. Update app.py
See: `app_mongo.py` for full MongoDB implementation

### 5. Update Docker Setup
Add MongoDB service to `docker-compose.yml` and `docker-compose.prod.yml`

## Advanced Features with MongoDB

### Ingredient Aggregation
```python
# Count ingredients across all recipes
pipeline = [
    {"$unwind": "$ingredients"},
    {"$group": {
        "_id": "$ingredients.item",
        "count": {"$sum": 1},
        "recipes": {"$addToSet": "$title"}
    }},
    {"$sort": {"count": -1}}
]
```

### Smart Recipe Selection
```python
# Find recipes with specific ingredients
recipes = db.recipes.find({
    "ingredients.item": {"$in": ["chicken", "garlic"]}
})

# Find recipes by cooking method and portions
recipes = db.recipes.find({
    "stove": True,
    "portions": {"$gte": 4}
})
```

### Meal Planning
```python
# Track weekly meal plans
{
  _id: ObjectId("..."),
  week_start: ISODate("2025-01-19"),
  meals: [
    {
      date: ISODate("2025-01-19"),
      recipe_id: ObjectId("..."),
      weather: {"condition": "Sunny", "temp": 75}
    }
  ],
  grocery_list_generated: ISODate("2025-01-19")
}
```

## Testing Strategy

1. **Parallel Run**: Keep recipes.json, add MongoDB alongside
2. **Compare Results**: Verify MongoDB returns same data
3. **Gradual Migration**: Move one endpoint at a time
4. **Backup**: Export MongoDB to JSON regularly
5. **Rollback Plan**: Keep recipes.json for 30 days

## Performance Tips

- Index on `title`, `ingredients.item`, `tags`
- Use projection to return only needed fields
- Cache frequent queries (weather-based selections)
- Use MongoDB aggregation pipeline for grocery lists

## Next Steps

1. Run `migrate_to_mongo.py` to import existing recipes
2. Test MongoDB queries work correctly
3. Update `app.py` to use MongoDB
4. Add new features (tags, search, filtering)
5. Deploy with MongoDB container/cloud connection
