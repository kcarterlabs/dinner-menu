#!/usr/bin/env python3
"""
Comprehensive error monitoring and testing script for the dinner menu app
Captures errors, logs them, and provides detailed debugging information
"""

import requests
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:5000"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class ErrorMonitor:
    def __init__(self):
        self.errors = []
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
    
    def log_error(self, test_name, error_type, error_msg, details=None):
        """Log an error with full context"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'error_type': error_type,
            'error_message': error_msg,
            'details': details or {}
        }
        self.errors.append(error_entry)
        
        # Print to console
        print(f"\n❌ FAILED: {test_name}")
        print(f"   Error: {error_type}: {error_msg}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)[:200]}")
    
    def test_endpoint(self, name, method, endpoint, data=None, expected_status=200):
        """Test an API endpoint and capture any errors"""
        self.tests_run += 1
        
        try:
            url = f"{API_BASE_URL}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=5)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=5)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, timeout=5)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code != expected_status:
                self.tests_failed += 1
                self.log_error(
                    name,
                    f"StatusError ({response.status_code})",
                    f"Expected {expected_status}, got {response.status_code}",
                    {
                        'response': response.text[:500],
                        'url': url,
                        'method': method
                    }
                )
                return False
            
            # Status code matches expected - check if it's an error status
            if expected_status >= 400:
                # We expected an error response and got it with the right status
                self.tests_passed += 1
                print(f"✅ PASSED: {name} (correctly returned {response.status_code})")
                return True
            
            # Check if response is valid JSON
            try:
                response_data = response.json()
                
                # Check for error in response
                if not response_data.get('success', True):
                    self.tests_failed += 1
                    self.log_error(
                        name,
                        "APIError",
                        response_data.get('error', 'Unknown error'),
                        {'response': response_data}
                    )
                    return False
                
                self.tests_passed += 1
                print(f"✅ PASSED: {name}")
                return True
                
            except json.JSONDecodeError as e:
                self.tests_failed += 1
                self.log_error(
                    name,
                    "JSONDecodeError",
                    str(e),
                    {'response_text': response.text[:500]}
                )
                return False
                
        except requests.exceptions.Timeout:
            self.tests_failed += 1
            self.log_error(
                name,
                "TimeoutError",
                "Request timed out after 5 seconds",
                {'url': url}
            )
            return False
            
        except requests.exceptions.ConnectionError as e:
            self.tests_failed += 1
            self.log_error(
                name,
                "ConnectionError",
                "Could not connect to API",
                {'error': str(e), 'url': url}
            )
            return False
            
        except Exception as e:
            self.tests_failed += 1
            self.log_error(
                name,
                type(e).__name__,
                str(e),
                {'traceback': traceback.format_exc()}
            )
            return False
    
    def save_report(self):
        """Save error report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = LOG_DIR / f"error_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'tests_run': self.tests_run,
                'tests_passed': self.tests_passed,
                'tests_failed': self.tests_failed,
                'pass_rate': f"{(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%"
            },
            'errors': self.errors
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📝 Report saved to: {report_file}")
        except (PermissionError, IOError) as e:
            # Try to save to current directory instead
            report_file = Path(f"error_report_{timestamp}.json")
            try:
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"\n📝 Report saved to: {report_file}")
            except Exception:
                print(f"\n⚠️  Could not save report to file: {e}")
                print("\n📄 Report Contents:")
                print(json.dumps(report, indent=2))
        
        return report_file


def main():
    """Run comprehensive tests"""
    print("="*70)
    print("🔍 Dinner Menu Error Monitor & Test Suite")
    print("="*70)
    print()
    
    monitor = ErrorMonitor()
    
    # Test 1: Health check
    print("\n📋 Testing API Health...")
    monitor.test_endpoint(
        "API Health Check",
        "GET",
        "/api/health"
    )
    
    # Test 2: Get recipes
    print("\n📋 Testing Get Recipes...")
    monitor.test_endpoint(
        "Get Recipes",
        "GET",
        "/api/recipes"
    )
    
    # Test 3: Parse ingredients - simple
    print("\n📋 Testing Bulk Import - Simple...")
    monitor.test_endpoint(
        "Parse Simple Ingredients",
        "POST",
        "/api/parse-ingredients",
        data={
            'ingredients': [
                '1 yellow onion',
                '2 cloves garlic'
            ]
        }
    )
    
    # Test 4: Parse ingredients - complex with prices
    print("\n📋 Testing Bulk Import - With Prices...")
    monitor.test_endpoint(
        "Parse Ingredients with Prices",
        "POST",
        "/api/parse-ingredients",
        data={
            'ingredients': [
                '▢ 1 yellow onion ($0.70)',
                '▢ 2 cloves garlic ($0.08)',
                '▢ 1 Tbsp olive oil ($0.22)',
                '▢ 1 lb. ground beef ($4.98)'
            ]
        }
    )
    
    # Test 5: Parse ingredients - edge cases
    print("\n📋 Testing Bulk Import - Edge Cases...")
    monitor.test_endpoint(
        "Parse Edge Case Ingredients",
        "POST",
        "/api/parse-ingredients",
        data={
            'ingredients': [
                '',  # Empty string
                '   ',  # Whitespace only
                'salt to taste',  # No quantity
                '2-3 cloves garlic',  # Range
                '1/2 cup flour'  # Fraction
            ]
        }
    )
    
    # Test 6: Parse ingredients - invalid input
    print("\n📋 Testing Bulk Import - Invalid Input...")
    monitor.test_endpoint(
        "Parse Invalid Input (should fail gracefully)",
        "POST",
        "/api/parse-ingredients",
        data={'ingredients': 'not a list'},
        expected_status=400
    )
    
    # Test 7: Parse ingredients - empty list
    print("\n📋 Testing Bulk Import - Empty List...")
    monitor.test_endpoint(
        "Parse Empty List",
        "POST",
        "/api/parse-ingredients",
        data={'ingredients': []}
    )
    
    # Test 8: Add recipe - datetime serialization
    print("\n📋 Testing Recipe Creation - DateTime Serialization...")
    monitor.test_endpoint(
        "Add Recipe with Ingredients",
        "POST",
        "/api/recipes",
        data={
            'title': 'Error Monitor Test Recipe',
            'date': '2026-01-20',
            'ingredients': [
                {
                    'quantity': '1',
                    'unit': '',
                    'item': 'test ingredient',
                    'original': '1 test ingredient'
                }
            ],
            'oven': False,
            'stove': True,
            'portions': '2'
        },
        expected_status=201
    )
    
    # Print summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"Tests Run:    {monitor.tests_run}")
    print(f"Passed:       {monitor.tests_passed} ✅")
    print(f"Failed:       {monitor.tests_failed} ❌")
    
    if monitor.tests_run > 0:
        pass_rate = (monitor.tests_passed / monitor.tests_run) * 100
        print(f"Pass Rate:    {pass_rate:.1f}%")
    
    # Save report
    report_file = monitor.save_report()
    
    # Exit with error code if any tests failed
    if monitor.tests_failed > 0:
        print(f"\n⚠️  {monitor.tests_failed} test(s) failed. Check the report for details.")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
