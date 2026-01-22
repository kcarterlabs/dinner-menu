# Agents Documentation

## Overview

This document describes the agent architecture and patterns for the dinner-menu application. Agents are autonomous or semi-autonomous components that perform specific tasks, respond to events, or coordinate complex workflows.

## Agent Types

### 1. Recipe Scraping Agent
**Purpose**: Automatically discover and import recipes from various sources.

**Capabilities**:
- Crawl recipe websites using `recipe-scrape.py`
- Parse structured recipe data
- Validate ingredient lists and instructions
- Auto-categorize recipes by cuisine, difficulty, or meal type

**Usage**:
```python
from recipe_scrape import RecipeScraper

agent = RecipeScraper(target_urls=['https://example.com/recipes'])
recipes = agent.scrape_and_parse()
agent.import_to_database(recipes)
```

### 2. Ingredient Suggestion Agent
**Purpose**: Provide intelligent ingredient recommendations and substitutions.

**Capabilities**:
- Suggest alternative ingredients based on dietary restrictions
- Recommend seasonal substitutions
- Calculate nutritional impacts of substitutions
- Handle allergen replacements

**Implementation**: See `demo_ingredient_suggestions.py` and `INGREDIENT_SUGGESTION_FEATURE.md`

**Usage**:
```python
from ingredient_parser import get_ingredient_suggestions

suggestions = get_ingredient_suggestions(
    ingredient="butter",
    dietary_restrictions=["vegan"],
    context="baking"
)
```

### 3. Menu Planning Agent
**Purpose**: Intelligently generate weekly menu plans based on constraints.

**Capabilities**:
- Balance nutritional requirements across meals
- Optimize ingredient usage to minimize waste
- Consider user preferences and dietary restrictions
- Generate shopping lists automatically

**Example**:
```python
class MenuPlanningAgent:
    def __init__(self, db_connection, user_preferences):
        self.db = db_connection
        self.preferences = user_preferences
    
    def generate_weekly_plan(self, constraints):
        """
        Generate a 7-day menu plan
        
        Args:
            constraints: dict with keys like 'max_budget', 'dietary_restrictions', 
                        'preferred_cuisines', 'servings_per_meal'
        
        Returns:
            dict: Weekly meal plan with recipes and shopping list
        """
        pass
```

### 4. Reroll Agent
**Purpose**: Handle recipe reroll requests with intelligent suggestions.

**Capabilities**:
- Track reroll history to avoid repeated suggestions
- Consider previous rejections when suggesting alternatives
- Balance variety with user preferences
- Support individual recipe rerolls

**Implementation**: See `REROLL_FEATURE.md` and `INDIVIDUAL_REROLL_FEATURE.md`

### 5. Database Maintenance Agent
**Purpose**: Automated database health checks and cleanup.

**Capabilities**:
- Clean up test data (`cleanup_test_recipes.py`)
- Perform automated backups (`backup_mongodb.sh`)
- Monitor database performance
- Detect and fix data inconsistencies

**Usage**:
```bash
# Manual cleanup
python cleanup_test_recipes.py

# Automated backup
./backup_mongodb.sh
```

## Agent Communication Patterns

### Event-Driven Architecture

Agents can respond to application events:

```python
from event_bus import EventBus

class RecipeUpdateAgent:
    def __init__(self):
        EventBus.subscribe('recipe.created', self.on_recipe_created)
        EventBus.subscribe('recipe.updated', self.on_recipe_updated)
    
    def on_recipe_created(self, event):
        recipe = event.data
        # Validate recipe structure
        # Generate thumbnails
        # Update search index
        pass
    
    def on_recipe_updated(self, event):
        # Invalidate caches
        # Notify subscribers
        pass
```

### Request-Response Pattern

For synchronous operations:

```python
class IngredientValidationAgent:
    def validate(self, ingredients):
        """Validate ingredient list format and content"""
        errors = []
        for ingredient in ingredients:
            if not self._is_valid_format(ingredient):
                errors.append(f"Invalid format: {ingredient}")
        return {'valid': len(errors) == 0, 'errors': errors}
```

### Background Task Pattern

For long-running operations:

```python
from celery import Celery

app = Celery('dinner_menu')

@app.task
def import_recipes_from_url(url):
    """Background task for importing recipes"""
    scraper = RecipeScraper([url])
    recipes = scraper.scrape_and_parse()
    return scraper.import_to_database(recipes)
```

## Agent Implementation Guidelines

### 1. Single Responsibility
Each agent should have one clear purpose. Don't create god-agents that do everything.

### 2. Error Handling
Agents should be resilient and handle errors gracefully:

```python
class RobustAgent:
    def __init__(self):
        self.error_monitor = ErrorMonitor()  # See error_monitor.py
    
    def execute_task(self):
        try:
            # Task execution
            pass
        except Exception as e:
            self.error_monitor.log_error(e)
            # Implement retry logic or fallback behavior
            pass
```

### 3. Logging and Monitoring
All agents should implement comprehensive logging:

```python
import logging

logger = logging.getLogger(__name__)

class MonitoredAgent:
    def process(self, data):
        logger.info(f"Processing started: {len(data)} items")
        try:
            result = self._do_work(data)
            logger.info(f"Processing completed successfully")
            return result
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            raise
```

### 4. Configuration Management
Agents should be configurable without code changes:

```python
import os

class ConfigurableAgent:
    def __init__(self):
        self.api_key = os.getenv('RECIPE_API_KEY')
        self.rate_limit = int(os.getenv('SCRAPER_RATE_LIMIT', '10'))
        self.timeout = int(os.getenv('SCRAPER_TIMEOUT', '30'))
```

## Testing Agents

### Unit Tests
Test agent logic in isolation:

```python
# tests/test_agents.py
import pytest
from agents.ingredient_suggestion import IngredientSuggestionAgent

def test_vegan_butter_substitution():
    agent = IngredientSuggestionAgent()
    suggestions = agent.suggest_alternatives('butter', dietary=['vegan'])
    
    assert len(suggestions) > 0
    assert any('coconut oil' in s.lower() for s in suggestions)
```

### Integration Tests
Test agent interactions with the database and other services:

```python
# tests/test_agent_integration.py
def test_recipe_import_agent(test_db):
    agent = RecipeImportAgent(db=test_db)
    result = agent.import_recipe(sample_recipe_data)
    
    assert result.success
    assert test_db.recipes.count_documents({}) == 1
```

### End-to-End Tests
Test complete agent workflows:

```bash
# See test_mongodb_integration.sh for example patterns
./test_mongodb_integration.sh
```

## Deployment Considerations

### Docker Integration
Agents can run as separate containers:

```dockerfile
# Dockerfile.agent-worker
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agents/ ./agents/
CMD ["python", "-m", "agents.worker"]
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
services:
  agent-worker:
    build:
      context: .
      dockerfile: Dockerfile.agent-worker
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - mongodb
      - redis
```

## Monitoring and Debugging

### Error Reports
Agent errors are logged to `error_report_*.json` files. See `error_monitor.py` for details.

### Status Checks
Use `status_check.sh` to verify agent health:

```bash
./status_check.sh
```

### Diagnostic Tools
```bash
./diagnose.sh  # Run comprehensive diagnostics
```

## Future Agent Ideas

### 1. Nutrition Analysis Agent
- Calculate nutritional information for recipes
- Suggest modifications to meet health goals
- Track macro/micronutrient balance

### 2. Shopping List Optimization Agent
- Group items by store section
- Find best prices across stores
- Suggest bulk buying opportunities

### 3. Meal Prep Coordinator Agent
- Optimize cooking order for efficiency
- Identify batch cooking opportunities
- Generate prep schedules

### 4. Social Integration Agent
- Share recipes to social media
- Import recipes from shared links
- Coordinate group meal planning

### 5. Learning Agent
- Track which recipes users cook most
- Learn preferences over time
- Improve suggestions based on feedback

## Related Documentation

- [API Documentation](API_README.md)
- [Ingredient Suggestions](INGREDIENT_SUGGESTION_FEATURE.md)
- [Reroll Feature](REROLL_FEATURE.md)
- [Individual Reroll](INDIVIDUAL_REROLL_FEATURE.md)
- [Testing Guide](TESTING_README.md)
- [MongoDB Integration](MONGODB_MIGRATION.md)

## Contributing

When creating new agents:
1. Document the agent's purpose and capabilities here
2. Add unit tests in `tests/test_agents.py`
3. Update integration tests if needed
4. Add configuration options to environment variables
5. Update docker-compose if agent requires separate container
6. Add monitoring and error handling

## Support

For questions or issues with agents, check:
- Error logs in `logs/` directory
- Error reports: `error_report_*.json`
- Test output: `test_output.txt`
- Run diagnostics: `./diagnose.sh`
