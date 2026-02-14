"""FatSecret Platform API integration using OAuth 1.0."""
import requests
import os
import time
import hashlib
import hmac
import base64
from urllib.parse import quote, urlencode
import secrets

class FatSecretService:
    """Service for interacting with FatSecret Platform API using OAuth 1.0."""
    
    BASE_URL = "https://platform.fatsecret.com/rest/server.api"
    
    def __init__(self):
        self.consumer_key = os.getenv('FATSECRET_CLIENT_ID')
        self.consumer_secret = os.getenv('FATSECRET_CLIENT_SECRET')
    
    def _generate_oauth_signature(self, method, url, params):
        """Generate OAuth 1.0 signature."""
        # Sort parameters
        sorted_params = sorted(params.items())
        
        # Create parameter string
        param_string = '&'.join([f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in sorted_params])
        
        # Create signature base string
        signature_base = f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"
        
        # Create signing key
        signing_key = f"{quote(self.consumer_secret, safe='')}&"
        
        # Generate signature
        signature = hmac.new(
            signing_key.encode(),
            signature_base.encode(),
            hashlib.sha1
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    def _make_request(self, params):
        """Make authenticated request to FatSecret API."""
        # Add OAuth parameters
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': secrets.token_hex(16),
            'oauth_version': '1.0',
            'format': 'json'
        }
        
        # Combine with request parameters
        all_params = {**oauth_params, **params}
        
        # Generate signature
        signature = self._generate_oauth_signature('GET', self.BASE_URL, all_params)
        all_params['oauth_signature'] = signature
        
        # Make request
        response = requests.get(self.BASE_URL, params=all_params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.text}")
    
    def search_food(self, query, max_results=20):
        """
        Search for food by name.
        
        Args:
            query: Search term
            max_results: Maximum number of results
            
        Returns:
            List of food items with nutrition info
        """
        params = {
            'method': 'foods.search',
            'search_expression': query,
            'max_results': max_results
        }
        
        data = self._make_request(params)
        
        if 'foods' in data and 'food' in data['foods']:
            foods = data['foods']['food']
            # Ensure it's a list
            if isinstance(foods, dict):
                foods = [foods]
            return foods
        return []
    
    def get_food_details(self, food_id):
        """
        Get detailed nutrition information for a specific food.
        
        Args:
            food_id: FatSecret food ID
            
        Returns:
            Detailed food information
        """
        params = {
            'method': 'food.get.v2',
            'food_id': food_id
        }
        
        return self._make_request(params)
    
    def search_by_barcode(self, barcode):
        """
        Search for food by barcode (UPC/EAN).
        
        Args:
            barcode: Product barcode
            
        Returns:
            Food information
        """
        params = {
            'method': 'food.find_id_for_barcode',
            'barcode': barcode
        }
        
        data = self._make_request(params)
        
        if 'food_id' in data and 'food_id' in data['food_id']:
            food_id = data['food_id']['value']
            # Get full details for this food
            return self.get_food_details(food_id)
        return None
    
    @staticmethod
    def parse_food_item(food_data):
        """
        Parse FatSecret food data into our format.
        
        Args:
            food_data: Raw food data from FatSecret
            
        Returns:
            Parsed food information
        """
        # Handle both search results and detailed food info
        if 'food' in food_data:
            food = food_data['food']
        else:
            food = food_data
        
        # Get servings
        servings = []
        default_serving = {}
        
        if 'servings' in food and 'serving' in food['servings']:
            serving_data = food['servings']['serving']
            # Handle both single serving and multiple servings
            if isinstance(serving_data, list):
                servings = serving_data
            else:
                servings = [serving_data]
            default_serving = servings[0] if servings else {}
        elif 'food_description' in food:
            # Parse description from search results (format: "Per 100g - Calories: 52kcal | Fat: 0.17g | Carbs: 13.81g | Protein: 0.26g")
            desc = food['food_description']
            default_serving = {
                'serving_description': desc.split(' - ')[0] if ' - ' in desc else 'Per serving',
                'calories': 0,
                'protein': 0,
                'carbohydrate': 0,
                'fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0
            }
            
            # Try to parse nutrition from description
            try:
                if 'Calories:' in desc:
                    cal_part = desc.split('Calories:')[1].split('|')[0].strip()
                    default_serving['calories'] = float(cal_part.replace('kcal', '').strip())
                if 'Protein:' in desc:
                    prot_part = desc.split('Protein:')[1].split('|')[0].strip() if '|' in desc.split('Protein:')[1] else desc.split('Protein:')[1].strip()
                    default_serving['protein'] = float(prot_part.replace('g', '').strip())
                if 'Carbs:' in desc:
                    carb_part = desc.split('Carbs:')[1].split('|')[0].strip()
                    default_serving['carbohydrate'] = float(carb_part.replace('g', '').strip())
                if 'Fat:' in desc:
                    fat_part = desc.split('Fat:')[1].split('|')[0].strip()
                    default_serving['fat'] = float(fat_part.replace('g', '').strip())
            except:
                pass
        
        return {
            'food_id': food.get('food_id'),
            'food_name': food.get('food_name'),
            'brand_name': food.get('brand_name'),
            'food_type': food.get('food_type'),
            'food_url': food.get('food_url'),
            'servings': servings,
            'default_serving': {
                'serving_description': default_serving.get('serving_description', 'Per serving'),
                'serving_size': float(default_serving.get('metric_serving_amount', 0)) if default_serving.get('metric_serving_amount') else None,
                'calories': float(default_serving.get('calories', 0)),
                'protein': float(default_serving.get('protein', 0)),
                'carbohydrates': float(default_serving.get('carbohydrate', 0)),
                'fat': float(default_serving.get('fat', 0)),
                'fiber': float(default_serving.get('fiber', 0)),
                'sugar': float(default_serving.get('sugar', 0)),
                'sodium': float(default_serving.get('sodium', 0))
            }
        }
