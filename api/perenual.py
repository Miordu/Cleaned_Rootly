"""
Integration with the Perenual API to fetch real plant data.
"""

import os
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment
API_KEY = os.environ.get('PERENUAL_API_KEY')
BASE_URL = "https://perenual.com/api/v2"

def get_plant_list(page=1, size=20, edible=0):
    """Fetch plant list from the Perenual API."""
    try:
        params = {
            "key": API_KEY,
            "page": page,
            "size": size,
            "edible": edible
        }
        response = requests.get(f"{BASE_URL}/species-list", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching plant list: {e}")
        return {"data": []}  # Return empty data on error

def get_plant_details(plant_id):
    """Fetch plant details from the Perenual API."""
    try:
        params = {"key": API_KEY}
        response = requests.get(f"{BASE_URL}/species/details/{plant_id}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching plant details: {e}")
        return {}  # Return empty object on error

def search_plants(query):
    """Search plants using the Perenual API."""
    try:
        params = {
            "key": API_KEY,
            "q": query
        }
        response = requests.get(f"{BASE_URL}/species-list", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching plants: {e}")
        return {"data": []}  # Return empty data on error
def get_care_guide(plant_id):
    """Fetch care guide from the Perenual API."""
    try:
        response = requests.get(f"{BASE_URL}/plants/{plant_id}/care", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching care guide: {e}")
        return {"data": []}  # Return empty data on error

def map_plant_to_model(perenual_data):
    """Map Perenual API data to model structure."""
    return {
        'scientific_name': perenual_data.get('scientific_name', 'Unknown'),
        'common_name': perenual_data.get('common_name', 'Unknown Plant'),
        'description': perenual_data.get('description', 'No description available.'),
        'indoor': perenual_data.get('indoor', False),
        'data_sources': ['Perenual']
    }

def map_care_to_model(perenual_care_data):
    """Map care data from Perenual API to model structure."""
    return {
        'watering_frequency': perenual_care_data.get('watering', 'Weekly'),
        'sunlight_requirements': [section['description'] for section in perenual_care_data if section['section'] == 'sunlight'],
        'soil_preferences': perenual_care_data.get('soil', 'Well-draining potting mix'),
        'temperature_range': perenual_care_data.get('temperature', '65-80°F'),
        'difficulty_level': perenual_care_data.get('difficulty', 'Easy')
    }
