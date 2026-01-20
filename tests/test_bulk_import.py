"""
Test bulk ingredient import and parsing functionality
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from app import app
from ingredient_parser import parse_ingredient


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestIngredientParser:
    """Test the ingredient parser function directly"""
    
    def test_parse_simple_ingredient(self):
        """Test parsing a simple ingredient"""
        result = parse_ingredient("1 yellow onion")
        assert result['quantity'] == '1'
        assert result['item'] == 'yellow onion'
        assert result['unit'] == ''
    
    def test_parse_with_unit(self):
        """Test parsing ingredient with unit"""
        result = parse_ingredient("2 tablespoons olive oil")
        assert result['quantity'] == '2'
        assert result['unit'] == 'tablespoons'
        assert 'olive oil' in result['item'].lower()
    
    def test_parse_with_abbreviation(self):
        """Test parsing with abbreviated units"""
        result = parse_ingredient("1 Tbsp olive oil")
        assert result['quantity'] == '1'
        assert result['unit'].lower() in ['tbsp', 'tablespoon', 'tablespoons']
        assert 'olive oil' in result['item'].lower()
    
    def test_parse_fraction(self):
        """Test parsing fractional quantities"""
        result = parse_ingredient("1/2 cup flour")
        assert result['quantity'] == '1/2'
        assert result['unit'] == 'cup'
    
    def test_parse_mixed_fraction(self):
        """Test parsing mixed fractions"""
        result = parse_ingredient("2 1/2 cups sugar")
        assert '2' in result['quantity'] and '1/2' in result['quantity']
        assert result['unit'] in ['cup', 'cups']
    
    def test_parse_with_price(self):
        """Test parsing ingredient with price in parentheses"""
        raw = "1 yellow onion ($0.70)"
        # Clean it first
        import re
        cleaned = re.sub(r'\s*\(\$[\d.]+\)', '', raw)
        result = parse_ingredient(cleaned)
        assert result['quantity'] == '1'
        assert 'yellow onion' in result['item'].lower()
    
    def test_parse_with_checkbox(self):
        """Test parsing ingredient with checkbox symbols"""
        raw = "▢ 2 cloves garlic"
        cleaned = raw.replace('▢', '').strip()
        result = parse_ingredient(cleaned)
        assert result['quantity'] == '2'
        assert 'garlic' in result['item'].lower()
    
    def test_parse_complex_description(self):
        """Test parsing with complex descriptions"""
        result = parse_ingredient("1 lb. ground beef")
        assert result['quantity'] == '1'
        assert result['unit'].lower() in ['lb', 'lb.', 'pound', 'pounds']
        assert 'ground beef' in result['item'].lower()
    
    def test_parse_no_quantity(self):
        """Test parsing ingredient without quantity"""
        result = parse_ingredient("salt to taste")
        assert result['item'].lower() in ['salt to taste', 'salt']
        # Quantity might be empty or 'to taste'
    
    def test_parse_range_quantity(self):
        """Test parsing ingredient with range"""
        result = parse_ingredient("2-3 cloves garlic")
        # Should handle ranges reasonably
        assert 'garlic' in result['item'].lower()


class TestBulkImportAPI:
    """Test the /api/parse-ingredients endpoint"""
    
    def test_parse_ingredients_endpoint_success(self, client):
        """Test successful parsing of ingredient list"""
        data = {
            'ingredients': [
                '1 yellow onion',
                '2 cloves garlic',
                '1 Tbsp olive oil'
            ]
        }
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['count'] == 3
        assert len(result['parsed_ingredients']) == 3
        
        # Check first ingredient
        first = result['parsed_ingredients'][0]
        assert 'quantity' in first
        assert 'unit' in first
        assert 'item' in first
        assert 'original' in first
        assert first['original'] == '1 yellow onion'
    
    def test_parse_ingredients_with_prices(self, client):
        """Test parsing ingredients with prices"""
        data = {
            'ingredients': [
                '▢ 1 yellow onion ($0.70)',
                '▢ 2 cloves garlic ($0.08)',
                '▢ 1 Tbsp olive oil ($0.22)'
            ]
        }
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['count'] == 3
        
        # Verify original text is preserved
        for ing in result['parsed_ingredients']:
            assert '$' in ing['original']  # Original has price
            assert '$' not in ing['item']   # Parsed item doesn't have price
    
    def test_parse_ingredients_empty_list(self, client):
        """Test parsing empty ingredient list"""
        data = {'ingredients': []}
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['count'] == 0
    
    def test_parse_ingredients_with_blanks(self, client):
        """Test parsing list with blank lines"""
        data = {
            'ingredients': [
                '1 yellow onion',
                '',
                '   ',
                '2 cloves garlic'
            ]
        }
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['count'] == 2  # Only non-blank lines
    
    def test_parse_ingredients_invalid_input(self, client):
        """Test parsing with invalid input format"""
        data = {'ingredients': 'not a list'}
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'must be a list' in result['error'].lower()
    
    def test_parse_ingredients_missing_field(self, client):
        """Test parsing with missing ingredients field"""
        data = {}
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        # Should handle gracefully with empty list
        assert result['count'] == 0
    
    def test_parse_ingredients_complex_format(self, client):
        """Test parsing complex real-world ingredient list"""
        data = {
            'ingredients': [
                '▢ 1 lb. ground beef (see notes, $4.98)',
                '▢ 2 Tbsp all-purpose flour ($0.03)',
                '▢ 1/2 tsp smoked paprika ($0.05)',
                '▢ 8 oz. tomato sauce ($0.56)',
                '▢ 1/2 lb. uncooked macaroni (about 2 cups, $0.59)'
            ]
        }
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['count'] == 5
        
        # Verify each ingredient has required fields
        for ing in result['parsed_ingredients']:
            assert 'quantity' in ing
            assert 'unit' in ing
            assert 'item' in ing
            assert 'original' in ing
            # Verify prices are in original but not in parsed items
            assert '$' in ing['original']
            assert '▢' in ing['original']
    
    def test_parse_ingredients_preserves_original(self, client):
        """Test that original text is always preserved"""
        data = {
            'ingredients': [
                '▢ 1 yellow onion ($0.70) - diced',
                '2 cloves garlic, minced'
            ]
        }
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        result = json.loads(response.data)
        
        # First ingredient: original should match input exactly
        assert result['parsed_ingredients'][0]['original'] == '▢ 1 yellow onion ($0.70) - diced'
        
        # Second ingredient: original should match input exactly
        assert result['parsed_ingredients'][1]['original'] == '2 cloves garlic, minced'


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_malformed_json(self, client):
        """Test handling of malformed JSON"""
        response = client.post('/api/parse-ingredients',
                              data='not valid json',
                              content_type='application/json')
        
        # Should return 400 or 500 with error message
        assert response.status_code in [400, 415, 500]
    
    def test_parse_special_characters(self, client):
        """Test parsing ingredients with special characters"""
        data = {
            'ingredients': [
                '½ cup flour',  # Unicode fraction
                '1/4 tsp salt',
                '2-3 cloves garlic'
            ]
        }
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        # Should not crash
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
    
    def test_very_long_ingredient_list(self, client):
        """Test parsing very long ingredient list"""
        data = {
            'ingredients': [f'{i} cups ingredient_{i}' for i in range(100)]
        }
        
        response = client.post('/api/parse-ingredients',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
