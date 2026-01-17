#!/bin/bash

# Run all tests
echo "🧪 Running unit tests..."

# Check if pytest-cov is installed
if python -c "import pytest_cov" 2>/dev/null; then
    # Run tests with coverage
    python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-report=xml
else
    # Run tests without coverage
    echo "⚠️  pytest-cov not installed, running without coverage"
    python -m pytest tests/ -v
fi

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Tests failed!"
    exit 1
fi
