#!/bin/bash

# Test runner for bulk import feature
# Captures detailed errors and logs

set -e

echo "=========================================="
echo "Testing Bulk Ingredient Import Feature"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}Warning: pytest not found. Installing...${NC}"
    pip install pytest pytest-json-report
fi

# Create logs directory
mkdir -p logs

# Run the tests with detailed output
echo "Running bulk import tests..."
echo ""

# Test with verbose output and capture to log file
if pytest tests/test_bulk_import.py -v --tb=short --json-report --json-report-file=logs/test_bulk_import_report.json 2>&1 | tee logs/test_bulk_import.log; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    TEST_RESULT=0
else
    echo ""
    echo -e "${RED}❌ Some tests failed. Check logs/test_bulk_import.log for details${NC}"
    TEST_RESULT=1
fi

# Show summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="

# Count test results
PASSED=$(grep -c "PASSED" logs/test_bulk_import.log || true)
FAILED=$(grep -c "FAILED" logs/test_bulk_import.log || true)
ERROR=$(grep -c "ERROR" logs/test_bulk_import.log || true)

echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Errors: $ERROR"
echo ""
echo "Full log: logs/test_bulk_import.log"
echo "JSON report: logs/test_bulk_import_report.json"
echo ""

# Show failed test details if any
if [ $FAILED -gt 0 ] || [ $ERROR -gt 0 ]; then
    echo -e "${RED}Failed Test Details:${NC}"
    grep -A 10 "FAILED\|ERROR" logs/test_bulk_import.log | head -50
fi

exit $TEST_RESULT
