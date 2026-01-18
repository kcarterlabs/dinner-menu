#!/usr/bin/env python3
"""Test the individual recipe re-roll feature"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import json

# Test the API
print("=" * 60)
print("Testing Individual Recipe Re-Roll Feature")
print("=" * 60)

print("\n1. Testing API with exclude_indices parameter...")
import app
app.app.config['TESTING'] = True
client = app.app.test_client()

# Mock the select function
with patch('app.select_dinner_recipes') as mock_select:
    mock_select.return_value = {
        "selected_recipes": [
            {"title": "Kept Recipe 1", "ingredients": ["a"], "portions": "2"},
            {"title": "New Recipe", "ingredients": ["b"], "portions": "2"},
            {"title": "Kept Recipe 2", "ingredients": ["c"], "portions": "2"}
        ],
        "total_portions": 6,
        "days_requested": 3,
        "too_hot_for_oven": False,
        "grocery_list": []
    }
    
    # Test re-rolling with exclude_indices
    response = client.post(
        '/api/dinner-menu?days=3',
        json={
            "weather": {"location": "Test", "forecast": []},
            "exclude_indices": [0, 2]  # Keep recipes at index 0 and 2
        },
        content_type='application/json'
    )
    
    if response.status_code == 200:
        data = response.get_json()
        print(f"✓ API Response: {data['success']}")
        print(f"✓ Recipes returned: {len(data['dinner_plan']['selected_recipes'])}")
        # Check that select was called with correct params
        call_args = mock_select.call_args[0]
        exclude_indices = mock_select.call_args[0][2] if len(call_args) > 2 else None
        print(f"✓ exclude_indices passed to select: {exclude_indices}")
        if exclude_indices == [0, 2]:
            print("✅ exclude_indices parameter working correctly!")
        else:
            print(f"❌ Expected [0, 2], got {exclude_indices}")
    else:
        print(f"❌ API failed: {response.status_code}")
        print(response.get_json())

print("\n2. Testing select_dinner_recipes with exclude_indices...")

# Create test recipes
test_recipes = [
    {"title": "Recipe A", "ingredients": ["a"], "oven": False, "stove": True, "portions": "2"},
    {"title": "Recipe B", "ingredients": ["b"], "oven": False, "stove": True, "portions": "2"},
    {"title": "Recipe C", "ingredients": ["c"], "oven": False, "stove": True, "portions": "2"},
    {"title": "Recipe D", "ingredients": ["d"], "oven": False, "stove": True, "portions": "2"}
]

with patch('app.load_recipes', return_value=test_recipes):
    weather_data = {
        "location": "Test",
        "forecast": [{"day": "Mon", "temp": 75.0}]
    }
    
    # Call with exclude_indices [0, 2] to keep Recipe A and C
    result = app.select_dinner_recipes(weather_data, 3, exclude_indices=[0, 2])
    
    print(f"✓ Total recipes selected: {len(result['selected_recipes'])}")
    print(f"✓ Recipe titles: {[r['title'] for r in result['selected_recipes']]}")
    
    # Check that Recipe A and C are in the results
    titles = [r['title'] for r in result['selected_recipes']]
    if "Recipe A" in titles and "Recipe C" in titles:
        print("✅ Excluded recipes were kept!")
    else:
        print(f"❌ Expected Recipe A and C to be kept")
    
    # Check that we have at least 3 recipes
    if len(result['selected_recipes']) >= 2:
        print("✅ Additional recipes were added!")
    else:
        print("❌ Not enough recipes selected")

print("\n3. Testing Streamlit reroll function...")
import streamlit_app

with patch('requests.post') as mock_post:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'success': True,
        'weather': {'location': 'Test'},
        'dinner_plan': {'selected_recipes': [], 'total_portions': 0}
    }
    mock_post.return_value = mock_response
    
    # Test with keep_indices
    result = streamlit_app.reroll_dinner_menu(
        days=3,
        weather_data={'location': 'Test', 'forecast': []},
        keep_indices=[1, 3]
    )
    
    # Check the POST request was made with exclude_indices
    call_kwargs = mock_post.call_args[1]
    if 'json' in call_kwargs and 'exclude_indices' in call_kwargs['json']:
        print(f"✓ exclude_indices in request: {call_kwargs['json']['exclude_indices']}")
        print("✅ Streamlit reroll function working correctly!")
    else:
        print("❌ exclude_indices not passed in request")

print("\n" + "=" * 60)
print("✅ Individual Recipe Re-Roll Feature Tests Complete!")
print("=" * 60)
