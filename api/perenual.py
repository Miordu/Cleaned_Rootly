"""
Placeholder module for Perenual API integration.
Currently disabled - returns mock data instead.
"""

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_plant_list(page=1, size=20, edible=0):
    """Return mock plant list data."""
    logger.info("Using mock data for plant list (Perenual API disabled)")
    return {
        "data": [
            {
                "id": 1,
                "common_name": "Example Plant",
                "scientific_name": ["Example scientific"],
                "cycle": "Perennial",
                "watering": "Average",
                "sunlight": ["full sun"]
            }
        ]
    }

def get_plant_details(plant_id):
    """Return mock plant details."""
    logger.info(f"Using mock data for plant details ID {plant_id} (Perenual API disabled)")
    return {
        "id": plant_id,
        "common_name": "Example Plant",
        "scientific_name": ["Example scientific"],
        "cycle": "Perennial",
        "watering": "Average",
        "sunlight": ["full sun"],
        "description": "This is a placeholder description since the Perenual API is currently disabled."
    }

def search_plants(query):
    """Return mock search results."""
    logger.info(f"Using mock data for plant search '{query}' (Perenual API disabled)")
    return {
        "data": [
            {
                "id": 1,
                "common_name": f"Search result for: {query}",
                "scientific_name": ["Example scientific"],
                "cycle": "Perennial",
                "watering": "Average",
                "sunlight": ["full sun"]
            }
        ]
    }

def get_care_guide(plant_id):
    """Return mock care guide data."""
    logger.info(f"Using mock data for care guide ID {plant_id} (Perenual API disabled)")
    return {
        "data": [
            {
                "section": "watering",
                "description": "Water regularly, allowing soil to dry between waterings."
            },
            {
                "section": "sunlight",
                "description": "Bright, indirect light"
            }
        ]
    }

def map_plant_to_model(perenual_data):
    """Map mock data to model structure."""
    return {
        'scientific_name': perenual_data.get('scientific_name', ['Unknown'])[0],
        'common_name': perenual_data.get('common_name', 'Unknown Plant'),
        'description': perenual_data.get('description', 'No description available.'),
        'indoor': True,
        'data_sources': ['mock']
    }

def map_care_to_model(perenual_care_data):
    """Map mock care data to model structure."""
    return {
        'watering_frequency': 'Weekly',
        'sunlight_requirements': ['Bright indirect light'],
        'soil_preferences': 'Well-draining potting mix',
        'temperature_range': '65-80°F',
        'difficulty_level': 'Easy'
    }
