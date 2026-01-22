# Data Protection Policy

## Production Data Files

The following files contain production data and **MUST NEVER** be modified by tests:

### Protected Files:
- `recipes.json` - Production recipe database
- `backups/` - Production backup files

## Test Isolation

All tests automatically use isolated test data:

### Test Data Location:
- `tests/test_data/test_recipes.json` - Test recipe file (auto-generated)
- `tests/test_data/test_backups/` - Test backup directory (auto-generated)

### How It Works:

1. **Automatic Isolation**: `tests/conftest.py` contains pytest fixtures that automatically:
   - Create a temporary test data directory
   - Redirect all file operations to test files
   - Clean up after each test

2. **No Manual Setup Required**: Every test automatically uses test data instead of production data

3. **Safety Guarantees**:
   - Production `recipes.json` is never read or modified during tests
   - Production `backups/` directory is never accessed during tests
   - Test data is cleaned up automatically after tests complete

## Running Tests Safely

```bash
# All tests use isolated test data automatically
./run_tests.sh

# Or run with pytest directly
python -m pytest tests/ -v
```

## For Developers

### Adding New Tests:

No special setup needed! Just write your test normally:

```python
def test_my_feature(test_client):
    # This automatically uses test_recipes.json, not production recipes.json
    response = test_client.post('/api/recipes', json={...})
    assert response.status_code == 201
```

### Available Fixtures:

- `test_recipes` - List of sample test recipe data
- `test_recipes_file` - Path to test recipes file
- `test_backup_dir` - Path to test backup directory
- `isolate_recipes_file` - Auto-applied to all tests, handles file isolation

### Verifying Isolation:

```bash
# Watch production files during test run
watch -n 1 'ls -lh recipes.json backups/'

# Run tests - you should see NO changes to these files
python -m pytest tests/test_e2e.py -v
```

## Emergency Recovery

If production data is accidentally modified:

```bash
# Restore from most recent backup
cp backups/recipes_YYYYMMDD_HHMMSS.json recipes.json

# Or restore from git
git checkout recipes.json
```

## CI/CD Pipeline

GitHub Actions workflow also uses isolated test data:
- Tests run in isolated environment
- Production data never exposed to CI
- Only code is pushed to ECR, never data
