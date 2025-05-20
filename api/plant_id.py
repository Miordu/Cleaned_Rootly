"""Module for interacting with the Plant.id API for plant identification."""

import os
import requests
import base64
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
PLANT_ID_API_KEY = os.environ.get('PLANT_ID_API_KEY')
BASE_URL = 'https://api.plant.id/v2'

def identify_plant(image_path, organs=None):
    """
    Identify a plant from an image using the Plant.id API.
    
    Args:
        image_path: Path to the image file
        organs: List of plant organs in the image ["flower", "leaf", "fruit", etc.]
    
    Returns:
        JSON response from the API
    """
    if not PLANT_ID_API_KEY:
        logger.error("Plant.id API key not found in environment variables")
        return {"error": "API key not configured"}
    
    try:
        # Read and encode the image
        with open(image_path, 'rb') as file:
            image_data = file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Prepare data for the API
        data = {
            'images': [base64_image],
            'modifiers': ["crops_fast", "similar_images"],
            'plant_language': 'en',
            'plant_details': ["common_names", "taxonomy", "url", "description", 
                             "image", "synonyms", "edible_parts", "watering", 
                             "propagation_methods"]
        }
        
        # Add plant organs if provided
        if organs:
            data['plant_organs'] = organs
        
        # Make API request
        headers = {
            'Content-Type': 'application/json',
            'Api-Key': PLANT_ID_API_KEY
        }
        
        response = requests.post(f"{BASE_URL}/identify", json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except FileNotFoundError:
        logger.error(f"Image file not found: {image_path}")
        return {"error": f"Image file not found: {image_path}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error identifying plant: {e}")
        return {"error": str(e)}

def identify_plant_from_binary(image_binary, organs=None):
    """
    Identify a plant from image binary data using the Plant.id API.
    
    Args:
        image_binary: Binary image data
        organs: List of plant organs in the image ["flower", "leaf", "fruit", etc.]
    
    Returns:
        JSON response from the API
    """
    if not PLANT_ID_API_KEY:
        logger.error("Plant.id API key not found in environment variables")
        return {"error": "API key not configured"}
    
    try:
        # Encode the binary image data
        base64_image = base64.b64encode(image_binary).decode('utf-8')
        
        # Prepare data for the API
        data = {
            'images': [base64_image],
            'modifiers': ["crops_fast", "similar_images"],
            'plant_language': 'en',
            'plant_details': ["common_names", "taxonomy", "url", "description", 
                             "image", "synonyms", "edible_parts", "watering", 
                             "propagation_methods"]
        }
        
        # Add plant organs if provided
        if organs:
            data['plant_organs'] = organs
        
        # Make API request
        headers = {
            'Content-Type': 'application/json',
            'Api-Key': PLANT_ID_API_KEY
        }
        
        response = requests.post(f"{BASE_URL}/identify", json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error identifying plant: {e}")
        return {"error": str(e)}

def map_identification_result(plant_id_data):
    """
    Map Plant.id API identification result to our application's data structure.
    
    Args:
        plant_id_data: Response from the Plant.id API
    
    Returns:
        Dictionary with structured plant data
    """
    if not plant_id_data or 'suggestions' not in plant_id_data or not plant_id_data['suggestions']:
        return {}
    
    # Get the most likely suggestion
    suggestion = plant_id_data['suggestions'][0]
    
    # Extract plant details
    plant_data = {
        'scientific_name': suggestion.get('plant_name'),
        'common_name': suggestion.get('plant_details', {}).get('common_names', [None])[0] if suggestion.get('plant_details', {}).get('common_names') else None,
        'confidence_score': suggestion.get('probability'),
        'image_url': suggestion.get('similar_images', [{}])[0].get('url') if suggestion.get('similar_images') else None,
    }
    
    # Add additional details if available
    if 'plant_details' in suggestion:
        details = suggestion['plant_details']
        plant_data.update({
            'description': details.get('description', {}).get('value') if isinstance(details.get('description'), dict) else details.get('description'),
            'taxonomy': details.get('taxonomy'),
            'edible_parts': details.get('edible_parts'),
            'watering': details.get('watering'),
            'propagation_methods': details.get('propagation_methods')
        })
    
    return plant_data