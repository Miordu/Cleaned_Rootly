"""Module for interacting with Plant identification APIs."""

import os
import requests
import base64
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PlantDotIDAPI:
    """Service class for identifying plants using Plant.id API (paid service)."""
    
    def __init__(self, api_key: str = None):
        self.base_url = "https://api.plant.id/v2"
        self.api_key = api_key or os.getenv('PLANT_ID_API_KEY')
        
        if not self.api_key:
            raise ValueError("Plant.id API key is required. Set PLANT_ID_API_KEY environment variable.")
    
    def identify_plant(self, image_file, modifiers: List[str] = None, 
                      plant_details: List[str] = None) -> Optional[Dict]:
        """
        Identify a plant using Plant.id API.
        
        Args:
            image_file: File object or file path or bytes
            modifiers: List of modifiers like ['crops_fast', 'similar_images']
            plant_details: List of details to include
        
        Returns:
            Dict containing identification results or None
        """
        if modifiers is None:
            modifiers = ["crops_fast", "similar_images"]
        
        if plant_details is None:
            plant_details = ["common_names", "url", "description", "taxonomy", "rank", "gbif_id"]
        
        # Prepare image data
        if hasattr(image_file, 'read'):
            image_data = image_file.read()
            image_file.seek(0)
        elif isinstance(image_file, str):
            with open(image_file, 'rb') as f:
                image_data = f.read()
        else:
            image_data = image_file
        
        encoded_image = base64.b64encode(image_data).decode('ascii')
        
        data = {
            "images": [encoded_image],
            "modifiers": modifiers,
            "plant_details": plant_details
        }
        
        headers = {
            "Content-Type": "application/json",
            "Api-Key": self.api_key
        }
        
        try:
            response = requests.post(f"{self.base_url}/identify", json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error identifying plant with Plant.id: {e}")
            return None


def identify_plant(image_path: str) -> Dict:
    """
    Main function called by Flask server to identify a plant from an image.
    
    Args:
        image_path: Path to the uploaded image file
        
    Returns:
        Dict containing identification results or error
    """
    try:
        # Try Plant.id API first
        plant_id_key = os.getenv('PLANT_ID_API_KEY')
        if plant_id_key:
            logger.info("Using Plant.id API for identification")
            api = PlantDotIDAPI(plant_id_key)
            result = api.identify_plant(image_path)
            if result:
                return result
        
        return {"error": "No plant identification API keys configured"}
    except Exception as e:
        logger.error(f"Error in plant identification: {str(e)}")
        return {"error": str(e)}


def map_identification_result(identification_result: Dict) -> Optional[Dict]:
    """
    Map the API identification result to a format expected by the Flask app.
    
    Args:
        identification_result: Raw result from the plant identification API
        
    Returns:
        Dict with standardized plant data or None
    """
    try:
        if 'suggestions' in identification_result and identification_result['suggestions']:
            # Plant.id API format
            suggestion = identification_result['suggestions'][0]
            plant_details = suggestion.get('plant_details', {})
            
            return {
                'scientific_name': suggestion.get('plant_name', ''),
                'common_names': plant_details.get('common_names', []),
                'confidence_score': suggestion.get('probability', 0),
                'family': plant_details.get('taxonomy', {}).get('family', ''),
                'genus': plant_details.get('taxonomy', {}).get('genus', ''),
                'api_source': 'plant_id'
            }
        
        logger.warning(f"Unknown identification result format: {identification_result}")
        return None
    except Exception as e:
        logger.error(f"Error mapping identification result: {str(e)}")
        return None
