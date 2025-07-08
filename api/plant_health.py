"""Module for interacting with the Plant.id API for health assessment."""

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

def assess_health(image_path):
    """
    Assess plant health from an image using the Plant.id API.
    
    Args:
        image_path: Path to the image file
    
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
            'modifiers': ["crops_fast"],
            'disease_details': ["description", "treatment", "classification"],
        }
        
        # Make API request
        headers = {
            'Content-Type': 'application/json',
            'Api-Key': PLANT_ID_API_KEY
        }
        
        response = requests.post(f"{BASE_URL}/health_assessment", json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except FileNotFoundError:
        logger.error(f"Image file not found: {image_path}")
        return {"error": f"Image file not found: {image_path}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error assessing plant health: {e}")
        return {"error": str(e)}

def assess_health_from_binary(image_binary):
    """
    Assess plant health from binary image data using the Plant.id API.
    
    Args:
        image_binary: Binary image data
    
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
            'modifiers': ["crops_fast"],
            'disease_details': ["description", "treatment", "classification"],
        }
        
        # Make API request
        headers = {
            'Content-Type': 'application/json',
            'Api-Key': PLANT_ID_API_KEY
        }
        
        response = requests.post(f"{BASE_URL}/health_assessment", json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error assessing plant health: {e}")
        return {"error": str(e)}

def map_health_assessment(health_data):
    """
    Map Plant.id API health assessment to our application's data structure.
    
    Args:
        health_data: Response from the Plant.id API health assessment
    
    Returns:
        Dictionary with structured health assessment data
    """
    if not health_data or 'health_assessment' not in health_data or 'diseases' not in health_data['health_assessment']:
        return {
            'is_healthy': True,
            'diseases': [],
            'diagnosis': 'Healthy plant',
            'treatment_recommendations': 'Continue regular care'
        }
    
    # Extract health assessment
    assessment = health_data['health_assessment']
    diseases = assessment.get('diseases', [])
    
    # If no diseases or high probability of being healthy
    if not diseases or (assessment.get('is_healthy') and assessment.get('is_healthy_probability', 0) > 0.7):
        return {
            'is_healthy': True,
            'diseases': [],
            'diagnosis': 'Healthy plant',
            'treatment_recommendations': 'Continue regular care'
        }
    
    # Get the most likely disease
    most_likely_disease = max(diseases, key=lambda d: d.get('probability', 0))
    
    # Extract symptoms
    symptoms = []
    if 'classification' in most_likely_disease and most_likely_disease['classification'].get('symptoms'):
        symptoms = most_likely_disease['classification'].get('symptoms')
    
    # Build health assessment
    health_assessment = {
        'is_healthy': False,
        'diseases': [disease.get('name') for disease in diseases if disease.get('probability', 0) > 0.3],
        'diagnosis': most_likely_disease.get('name', 'Unknown issue'),
        'symptoms': symptoms,
        'confidence_score': most_likely_disease.get('probability', 0),
        'treatment_recommendations': most_likely_disease.get('treatment', {}).get('overview', 'Consult a plant specialist')
    }
    
    return health_assessment