import requests
import os
import base64
from typing import Dict, List, Optional
from io import BytesIO
from PIL import Image
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PlantIDAPI:
    """Service class for identifying plants from images using PlantNet API v2."""
    
    def __init__(self, api_key: str = None):
        self.base_url = "https://my-api.plantnet.org/v2"
        self.api_key = api_key or os.getenv('PLANTNET_API_KEY')
        self.project = "all"  # Default project per PlantNet doc
        
        if not self.api_key:
            raise ValueError("PlantNet API key is required. Set PLANTNET_API_KEY environment variable.")
    
    def identify_plant(self, image_paths: List[str], organs: List[str] = None) -> Optional[Dict]:
        """
        Identify plants from image file paths using PlantNet API v2.
        
        Args:
            image_paths: List of image file paths
            organs: List of plant organs in the image (e.g., ['leaf', 'flower', 'fruit'])
        
        Returns:
            Dict containing identification results or None on failure
        """
        if organs is None:
            organs = ['auto']  # Let the API auto-detect
        
        url = f"{self.base_url}/identify/{self.project}"
        params = {'api-key': self.api_key}
        data = {'organs': organs}
        
        files = []
        try:
            for path in image_paths:
                files.append(('images', (os.path.basename(path), open(path, 'rb'), 'image/jpeg')))
            
            response = requests.post(url, params=params, data=data, files=files)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error identifying plant: {e}")
            return None
        finally:
            # Close all file handlers
            for _, file_tuple in files:
                file_tuple[1].close()

    def identify_plant_from_binary(self, image_bytes: bytes, organs: List[str] = None) -> Optional[Dict]:
        """
        Identify a plant from raw image bytes.
        
        Args:
            image_bytes: Raw image bytes
            organs: List of plant organs
        
        Returns:
            Dict with API identification results or None
        """
        if organs is None:
            organs = ['auto']
        
        url = f"{self.base_url}/identify/{self.project}"
        params = {'api-key': self.api_key}
        files = [('images', ('image.jpg', image_bytes, 'image/jpeg'))]
        data = {'organs': organs}
        
        try:
            response = requests.post(url, params=params, data=data, files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error identifying plant from binary: {e}")
            return None

    def get_top_matches(self, identification_result: Dict, top_n: int = 5) -> List[Dict]:
        """
        Extract top plant matches from identification result.
        
        Args:
            identification_result: Result from identify_plant()
            top_n: Number of top matches to return
        
        Returns:
            List of top plant matches with scores
        """
        if not identification_result or 'results' not in identification_result:
            return []
        
        results = identification_result['results']
        
        # Sort by score (confidence) and take top N
        sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
        
        top_matches = []
        for result in sorted_results[:top_n]:
            species = result.get('species', {})
            match_info = {
                'scientific_name': species.get('scientificNameWithoutAuthor', ''),
                'common_names': species.get('commonNames', []),
                'family': species.get('family', {}).get('scientificNameWithoutAuthor', ''),
                'genus': species.get('genus', {}).get('scientificNameWithoutAuthor', ''),
                'confidence_score': result.get('score', 0),
                'images': result.get('images', [])
            }
            top_matches.append(match_info)
        
        return top_matches


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
    
    def get_top_suggestions(self, identification_result: Dict, top_n: int = 5) -> List[Dict]:
        """Extract top plant suggestions from Plant.id result."""
        if not identification_result or 'suggestions' not in identification_result:
            return []
        
        suggestions = identification_result['suggestions'][:top_n]
        
        top_matches = []
        for suggestion in suggestions:
            plant_details = suggestion.get('plant_details', {})
            match_info = {
                'scientific_name': suggestion.get('plant_name', ''),
                'common_names': plant_details.get('common_names', []),
                'confidence_score': suggestion.get('probability', 0),
                'taxonomy': plant_details.get('taxonomy', {}),
                'description': plant_details.get('description', {}),
                'images': suggestion.get('similar_images', [])
            }
            top_matches.append(match_info)
        
        return top_matches


# Helper function for Flask integration
def identify_plant(image_path: str) -> Dict:
    """
    Main function called by Flask server to identify a plant from an image.
    
    Args:
        image_path: Path to the uploaded image file
        
    Returns:
        Dict containing identification results or error
    """
    try:
        plantnet_key = os.getenv('PLANTNET_API_KEY')
        if plantnet_key:
            logger.info("Using PlantNet API for identification")
            api = PlantIDAPI(plantnet_key)
            result = api.identify_plant([image_path])
            if result:
                return result
        
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


def identify_plant_from_binary(image_bytes: bytes, organs: List[str] = None) -> Dict:
    """
    Identify a plant from binary image data.
    
    Args:
        image_bytes: Raw image bytes
        organs: List of plant organs (optional)
        
    Returns:
        Dict with API identification results or error
    """
    plantnet_key = os.getenv('PLANTNET_API_KEY')
    if not plantnet_key:
        return {"error": "PlantNet API key is required."}
    
    api = PlantIDAPI(plantnet_key)
    result = api.identify_plant_from_binary(image_bytes, organs)
    if result:
        return result
    else:
        return {"error": "Failed to identify plant from binary data."}


def map_identification_result(identification_result: Dict) -> Optional[Dict]:
    """
    Map the API identification result to a format expected by the Flask app.
    
    Args:
        identification_result: Raw result from the plant identification API
        
    Returns:
        Dict with standardized plant data or None
    """
    try:
        if 'results' in identification_result:
            api = PlantIDAPI()
            top_matches = api.get_top_matches(identification_result, top_n=1)
            if top_matches:
                match = top_matches[0]
                return {
                    'scientific_name': match['scientific_name'],
                    'common_names': match['common_names'],
                    'family': match['family'],
                    'genus': match['genus'],
                    'confidence_score': match['confidence_score'],
                    'api_source': 'plantnet'
                }
        elif 'suggestions' in identification_result:
            api = PlantDotIDAPI()
            top_matches = api.get_top_suggestions(identification_result, top_n=1)
            if top_matches:
                match = top_matches[0]
                return {
                    'scientific_name': match['scientific_name'],
                    'common_names': match['common_names'],
                    'confidence_score': match['confidence_score'],
                    'family': match.get('taxonomy', {}).get('family', ''),
                    'genus': match.get('taxonomy', {}).get('genus', ''),
                    'api_source': 'plant_id'
                }
        logger.warning(f"Unknown identification result format: {identification_result}")
        return None
    except Exception as e:
        logger.error(f"Error mapping identification result: {str(e)}")
        return None


def resize_image_if_needed(image_file, max_size: int = 1024) -> Optional[bytes]:
    """
    Resize image if it's too large to reduce API call time and costs.
    
    Args:
        image_file: File object or bytes
        max_size: Maximum width/height in pixels
    
    Returns:
        Resized image as bytes or None on failure
    """
    try:
        if hasattr(image_file, 'read'):
            image = Image.open(image_file)
        else:
            image = Image.open(BytesIO(image_file))
        
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        output = BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return None
