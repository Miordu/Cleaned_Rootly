"""Module for interacting with the Trefle API for quantitative plant data."""

import os
import requests
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
TREFLE_API_KEY = os.environ.get('TREFLE_API_KEY')
BASE_URL = 'https://trefle.io/api/v1'

def get_plant_list(page=1, limit=20):
    """
    Get a list of plants from the Trefle API.
    
    Args:
        page: Page number for pagination
        limit: Number of results per page
    
    Returns:
        JSON response from the API
    """
    if not TREFLE_API_KEY:
        logger.error("Trefle API key not found in environment variables")
        return {"error": "API key not configured"}
    
    try:
        url = f"{BASE_URL}/plants"
        params = {
            'token': TREFLE_API_KEY,
            'page': page,
            'limit': limit
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching plant list: {e}")
        return {"error": str(e)}

def get_plant_details(plant_id):
    """
    Get detailed information about a specific plant.
    
    Args:
        plant_id: Trefle plant ID
    
    Returns:
        JSON response from the API
    """
    if not TREFLE_API_KEY:
        logger.error("Trefle API key not found in environment variables")
        return {"error": "API key not configured"}
    
    try:
        url = f"{BASE_URL}/plants/{plant_id}"
        params = {
            'token': TREFLE_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching plant details: {e}")
        return {"error": str(e)}

def search_plants(query):
    """
    Search for plants by name.
    
    Args:
        query: Search term
    
    Returns:
        JSON response from the API
    """
    if not TREFLE_API_KEY:
        logger.error("Trefle API key not found in environment variables")
        return {"error": "API key not configured"}
    
    try:
        url = f"{BASE_URL}/plants/search"
        params = {
            'token': TREFLE_API_KEY,
            'q': query
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching plants: {e}")
        return {"error": str(e)}

def get_growth_data(plant_id):
    """
    Get growth data for a specific plant.
    
    Args:
        plant_id: Trefle plant ID
    
    Returns:
        Dictionary with growth data
    """
    if not TREFLE_API_KEY:
        logger.error("Trefle API key not found in environment variables")
        return {"error": "API key not configured"}
    
    try:
        # Get plant details which include growth data
        plant_data = get_plant_details(plant_id)
        
        if 'data' not in plant_data or not plant_data['data']:
            return {"error": "No data found"}
        
        # Extract growth data
        growth_data = {}
        
        # Get data from specifications
        if 'main_species' in plant_data['data'] and 'specifications' in plant_data['data']['main_species']:
            specs = plant_data['data']['main_species']['specifications']
            growth_data.update({
                'average_height_cm': specs.get('average_height_cm'),
                'maximum_height_cm': specs.get('maximum_height_cm'),
                'growth_rate': specs.get('growth_rate'),
                'growth_habit': specs.get('growth_habit'),
                'growth_form': specs.get('growth_form'),
                'growth_months': specs.get('growth_months'),
                'bloom_months': specs.get('bloom_months'),
                'fruit_months': specs.get('fruit_months')
            })
        
        # Get data from growth
        if 'main_species' in plant_data['data'] and 'growth' in plant_data['data']['main_species']:
            growth = plant_data['data']['main_species']['growth']
            growth_data.update({
                'ph_minimum': growth.get('ph_minimum'),
                'ph_maximum': growth.get('ph_maximum'),
                'light': growth.get('light'),
                'atmospheric_humidity': growth.get('atmospheric_humidity'),
                'soil_nutriments': growth.get('soil_nutriments'),
                'soil_salinity': growth.get('soil_salinity'),
                'temperature_minimum_deg_c': growth.get('temperature_minimum', {}).get('deg_c'),
                'temperature_maximum_deg_c': growth.get('temperature_maximum', {}).get('deg_c')
            })
        
        return growth_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching growth data: {e}")
        return {"error": str(e)}

def map_growth_data_to_model(growth_data):
    """
    Map Trefle API growth data to our PlantCareDetails model structure.
    
    Args:
        growth_data: Growth data from get_growth_data()
    
    Returns:
        Dictionary with plant care details
    """
    if not growth_data or 'error' in growth_data:
        return {}
    
    # Map light to sunlight requirements
    sunlight_map = {
        0: ["Full shade"],
        1: ["Partial shade"],
        2: ["Partial shade"],
        3: ["Partial sun"],
        4: ["Partial sun"],
        5: ["Partial sun"],
        6: ["Full sun"],
        7: ["Full sun"],
        8: ["Full sun"],
        9: ["Full sun"],
        10: ["Full sun"]
    }
    
    light_level = growth_data.get('light')
    sunlight_requirements = sunlight_map.get(light_level, []) if light_level is not None else []
    
    # Map temperature range
    min_temp = growth_data.get('temperature_minimum_deg_c')
    max_temp = growth_data.get('temperature_maximum_deg_c')
    temperature_range = f"{min_temp}°C to {max_temp}°C" if min_temp is not None and max_temp is not None else None
    
    # Map growth rate to difficulty level
    growth_rate = growth_data.get('growth_rate')
    difficulty_level = None
    if growth_rate:
        if growth_rate.lower() == 'high':
            difficulty_level = 'Easy'
        elif growth_rate.lower() == 'moderate':
            difficulty_level = 'Intermediate'
        elif growth_rate.lower() == 'low':
            difficulty_level = 'Difficult'
    
    # Extract bloom months
    bloom_months = growth_data.get('bloom_months', [])
    
    # Create care details
    care_details = {
        'sunlight_requirements': sunlight_requirements,
        'temperature_range': temperature_range,
        'difficulty_level': difficulty_level,
        'growth_rate': growth_data.get('growth_rate'),
        'pruning_months': bloom_months,  # Use bloom months as pruning guidance
    }
    
    # Add soil preferences based on pH
    ph_min = growth_data.get('ph_minimum')
    ph_max = growth_data.get('ph_maximum')
    if ph_min is not None and ph_max is not None:
        if ph_min < 6.0:
            care_details['soil_preferences'] = 'Acidic soil (pH < 6.0)'
        elif ph_min >= 7.0:
            care_details['soil_preferences'] = 'Alkaline soil (pH > 7.0)'
        else:
            care_details['soil_preferences'] = 'Neutral soil (pH 6.0-7.0)'
    
    return care_details