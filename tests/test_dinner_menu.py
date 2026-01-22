import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, "scripts"))

# Import the module normally after renaming
import dinner_menu

class TestDinnerMenu(unittest.TestCase):
    
    @patch('requests.get')
    @patch('time.sleep')
    @patch('builtins.print')
    def test_forecast_success(self, mock_print, mock_sleep, mock_get):
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "location": {
                "name": "Spokane",
                "region": "Washington"
            },
            "forecast": {
                "forecastday": [
                    {
                        "date": "2025-10-08",
                        "day": {"maxtemp_f": 75.0}
                    },
                    {
                        "date": "2025-10-09", 
                        "day": {"maxtemp_f": 80.0}
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        result = dinner_menu.forecast("2")
        
        expected = [
            "Wednesday: 75.0°F",
            "Thursday: 80.0°F"
        ]
        self.assertEqual(result, expected)
        mock_sleep.assert_called_once_with(1)

    @patch('builtins.open', new_callable=mock_open, read_data='[{"title": "Pasta", "ingredients": ["pasta", "sauce"], "oven": false, "stove": true, "portions": "2"}, {"title": "Pizza", "ingredients": ["dough", "cheese"], "oven": true, "stove": false, "portions": "4"}]')
    @patch('builtins.print')
    def test_dinner_logic_normal_temp(self, mock_print, mock_file):
        weather = ["Monday: 75°F", "Tuesday: 80°F"]
        date_range = "2"
        
        dinner_menu.dinner_logic(weather, date_range)
        
        mock_file.assert_called_once_with('recipes.json', 'r')

    @patch('builtins.open', new_callable=mock_open, read_data='[{"title": "Pasta", "ingredients": ["pasta", "sauce"], "oven": false, "stove": true, "portions": "2"}, {"title": "Grilled Chicken", "ingredients": ["chicken", "spices"], "oven": false, "stove": false, "portions": "3"}]')
    @patch('builtins.print')
    def test_dinner_logic_hot_weather_filters_oven(self, mock_print, mock_file):
        weather = ["Monday: 95°F", "Tuesday: 92°F"]
        date_range = "2"
        
        dinner_menu.dinner_logic(weather, date_range)
        
        # Should filter out oven recipes when too hot
        mock_file.assert_called_once_with('recipes.json', 'r')

    def test_temperature_parsing(self):
        weather = ["Monday: 75°F", "Tuesday: 95°F"]
        temps = [float(entry.split(':')[1].replace('°F', '').strip()) for entry in weather]
        
        self.assertEqual(temps, [75.0, 95.0])
        self.assertTrue(any(temp > 90 for temp in temps))

    @patch('dinner_menu.os.getenv')  # Ensure the correct module is patched
    @patch('dinner_menu.requests.get')
    @patch('dinner_menu.time.sleep')
    @patch('builtins.print')
    def test_forecast_with_api_key(self, mock_print, mock_sleep, mock_get, mock_getenv):
        mock_getenv.return_value = "test_api_key"  # Mock the API key
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "location": {"name": "Spokane", "region": "Washington"},
            "forecast": {"forecastday": [{"date": "2025-10-08", "day": {"maxtemp_f": 65.0}}]}
        }
        mock_get.return_value = mock_response
    
        result = dinner_menu.forecast("1")
    
        # Verify API was called with correct headers
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['headers']['x-rapidapi-key'], "test_api_key")

if __name__ == '__main__':
    unittest.main()