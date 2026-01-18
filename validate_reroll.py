#!/usr/bin/env python3
"""Quick validation script for re-roll feature"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Import modules
print("✓ Test 1: Importing modules...")
try:
    import app
    import streamlit_app
    print("  ✓ Modules imported successfully")
except Exception as e:
    print(f"  ✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Check reroll function exists
print("\n✓ Test 2: Checking reroll_dinner_menu function...")
if hasattr(streamlit_app, 'reroll_dinner_menu'):
    print("  ✓ reroll_dinner_menu function exists")
else:
    print("  ✗ reroll_dinner_menu function not found")
    sys.exit(1)

# Test 3: Check API endpoint accepts POST
print("\n✓ Test 3: Checking API endpoint...")
app.app.config['TESTING'] = True
client = app.app.test_client()

# Test POST endpoint
from unittest.mock import patch

with patch('app.select_dinner_recipes') as mock_select:
    mock_select.return_value = {
        "selected_recipes": [],
        "total_portions": 0,
        "days_requested": 2,
        "too_hot_for_oven": False,
        "grocery_list": []
    }
    
    response = client.post(
        '/api/dinner-menu?days=2',
        json={"weather": {"location": "Test", "forecast": []}},
        content_type='application/json'
    )
    
    if response.status_code == 200:
        print("  ✓ POST /api/dinner-menu works")
    else:
        print(f"  ✗ POST /api/dinner-menu failed: {response.status_code}")
        print(f"     Response: {response.get_json()}")
        sys.exit(1)

# Test 4: Check session state management in streamlit
print("\n✓ Test 4: Checking session state structure...")
# This is just a check that the code structure is correct
import re
with open('streamlit_app.py', 'r') as f:
    content = f.read()
    if 'st.session_state.weather_menu_result' in content:
        print("  ✓ Session state for weather caching implemented")
    else:
        print("  ✗ Session state not found")
        sys.exit(1)
    
    if '🔄 Re-roll' in content:
        print("  ✓ Re-roll button implemented")
    else:
        print("  ✗ Re-roll button not found")
        sys.exit(1)

print("\n" + "="*50)
print("✅ All validation checks passed!")
print("="*50)
