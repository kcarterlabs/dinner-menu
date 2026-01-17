import pytest
import os
import json
import shutil
from unittest.mock import patch

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
TEST_RECIPES_FILE = os.path.join(TEST_DATA_DIR, 'test_recipes.json')
TEST_BACKUP_DIR = os.path.join(TEST_DATA_DIR, 'test_backups')

# Sample test recipes
TEST_RECIPES = [
    {
        "title": "Test Pasta",
        "ingredients": ["pasta", "tomato sauce", "garlic"],
        "oven": False,
        "stove": True,
        "portions": "2",
        "url": "https://example.com/pasta"
    },
    {
        "title": "Test Chicken",
        "ingredients": ["chicken", "spices", "vegetables"],
        "oven": True,
        "stove": False,
        "portions": "4",
        "url": "https://example.com/chicken"
    }
]


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Set up test environment once for all tests"""
    # Create test data directory
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    os.makedirs(TEST_BACKUP_DIR, exist_ok=True)
    
    yield
    
    # Cleanup after all tests
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)


@pytest.fixture(autouse=True)
def isolate_recipes_file(monkeypatch):
    """
    Automatically isolate recipes.json for all tests.
    Redirects all file operations to test-specific files.
    """
    # Patch the RECIPES_FILE constant in app module
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Create fresh test recipes file for each test
    with open(TEST_RECIPES_FILE, 'w') as f:
        json.dump(TEST_RECIPES, f, indent=4)
    
    # Patch app module constants
    try:
        import app
        monkeypatch.setattr(app, 'RECIPES_FILE', TEST_RECIPES_FILE)
        monkeypatch.setattr(app, 'BACKUP_DIR', TEST_BACKUP_DIR)
    except ImportError:
        pass
    
    # Patch add-recipe module constants
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("add_recipe", 
            os.path.join(parent_dir, "add-recipe.py"))
        add_recipe = importlib.util.module_from_spec(spec)
        monkeypatch.setattr(add_recipe, 'file_path', TEST_RECIPES_FILE)
        monkeypatch.setattr(add_recipe, 'backup_dir', TEST_BACKUP_DIR)
    except Exception:
        pass
    
    yield
    
    # Cleanup test recipes file after each test
    if os.path.exists(TEST_RECIPES_FILE):
        os.remove(TEST_RECIPES_FILE)
    
    # Cleanup test backups
    if os.path.exists(TEST_BACKUP_DIR):
        for file in os.listdir(TEST_BACKUP_DIR):
            os.remove(os.path.join(TEST_BACKUP_DIR, file))


@pytest.fixture
def test_recipes():
    """Provide test recipe data"""
    return TEST_RECIPES.copy()


@pytest.fixture
def test_recipes_file():
    """Provide path to test recipes file"""
    return TEST_RECIPES_FILE


@pytest.fixture
def test_backup_dir():
    """Provide path to test backup directory"""
    return TEST_BACKUP_DIR
