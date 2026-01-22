# Testing Guide

## Overview

This project includes comprehensive unit tests for all main components:
- `dinner_menu.py` - Weather-based menu logic
- `add-recipe.py` - Recipe management
- `app.py` - Flask API
- `streamlit_app.py` - Streamlit frontend helpers

## Running Tests Locally

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Simple test run
python -m pytest tests/

# With verbose output
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Or use the test script
chmod +x run_tests.sh
./run_tests.sh
```

### Run Specific Test Files

```bash
# Test only Flask API
python -m pytest tests/test_app.py -v

# Test only dinner menu logic
python -m pytest tests/test_dinner_menu.py -v

# Test only add-recipe functionality
python -m pytest tests/test_add_recipe.py -v

# Test only Streamlit helpers
python -m pytest tests/test_streamlit_app.py -v
```

### Run Specific Test Cases

```bash
# Run a specific test method
python -m pytest tests/test_app.py::TestFlaskAPI::test_health_endpoint -v

# Run tests matching a pattern
python -m pytest tests/ -k "recipe" -v
```

## Test Coverage

View coverage reports:

```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## GitHub Actions CI/CD

Tests run automatically on every push and pull request:

1. **Unit Tests** - All test suites run
2. **Coverage Report** - Code coverage calculated
3. **Docker Build** - Only proceeds if tests pass
4. **ECR Push** - Images pushed only after successful tests

### Workflow Steps

1. Checkout code
2. Set up Python 3.11
3. Install dependencies
4. **Run unit tests** ⭐
5. Upload coverage reports
6. Build Docker images (only if tests pass)
7. Push to ECR (only if tests pass)

## Test Structure

```
tests/
├── __init__.py
├── test_dinner_menu.py      # Tests for dinner_menu.py
├── test_add_recipe.py        # Tests for add-recipe.py
├── test_app.py               # Tests for Flask API
└── test_streamlit_app.py     # Tests for Streamlit helpers
```

## Writing New Tests

### Test Template

```python
import unittest
from unittest.mock import patch, MagicMock

class TestYourFeature(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def test_something(self):
        """Test description"""
        # Arrange
        expected = "value"
        
        # Act
        result = your_function()
        
        # Assert
        self.assertEqual(result, expected)
    
    @patch('module.function')
    def test_with_mock(self, mock_func):
        """Test with mocked dependency"""
        mock_func.return_value = "mocked"
        result = your_function()
        self.assertEqual(result, "mocked")
```

### Best Practices

1. **Name tests descriptively** - `test_add_recipe_with_missing_field`
2. **One assertion per test** - Test one thing at a time
3. **Use mocks for external dependencies** - Mock API calls, file I/O
4. **Test edge cases** - Empty inputs, invalid data, errors
5. **Keep tests fast** - Avoid real API calls or heavy operations

## Mocking Examples

### Mock HTTP Requests

```python
@patch('requests.get')
def test_api_call(self, mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'data': 'value'}
    mock_get.return_value = mock_response
    
    result = your_api_function()
    self.assertEqual(result['data'], 'value')
```

### Mock File Operations

```python
@patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
def test_file_read(self, mock_file):
    result = your_file_function()
    mock_file.assert_called_once_with('file.json', 'r')
```

### Mock Environment Variables

```python
@patch.dict(os.environ, {'API_KEY': 'test_key'})
def test_with_env_var(self):
    result = function_using_env_var()
    self.assertIn('test_key', result)
```

## Continuous Integration

### Required Tests Pass Criteria

- All test suites must pass (100% pass rate)
- No syntax errors
- No import errors
- All mocked dependencies work correctly

### On Test Failure

The GitHub Actions workflow will:
- ❌ Mark the build as failed
- 🛑 Stop before building Docker images
- 📝 Show detailed error messages
- 📊 Upload test results

Fix the failing tests before the Docker images will be built and pushed to ECR.

## Troubleshooting

### Tests fail locally but pass in CI

- Check Python version (CI uses 3.11)
- Check installed dependencies
- Clear pytest cache: `pytest --cache-clear`

### Import errors

- Ensure you're in the project root
- Check sys.path modifications in tests
- Verify __init__.py exists in tests/

### Mock not working

- Patch the correct module path
- Use `@patch` decorator in correct order
- Check mock is called with expected arguments

## Coverage Goals

- **Target**: 80%+ overall coverage
- **Critical paths**: 100% coverage for core logic
- **API endpoints**: All endpoints tested
- **Error handling**: All error cases tested
