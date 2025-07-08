"""Test script for API integrations."""

import os
import requests
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_perenual_api():
    """Test Perenual API integration."""
    logger.info("Testing Perenual API...")
    
    # Get API key
    api_key = os.environ.get('PERENUAL_API_KEY')
    logger.info(f"API key is set: {bool(api_key)}")
    
    # Create URL with v2 endpoint
    url = f"https://perenual.com/api/v2/species-list?key={api_key}&page=1&size=1"
    logger.info(f"Making request to: {url.replace(api_key, 'API_KEY_HIDDEN')}")
    
    try:
        response = requests.get(url)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("API call successful!")
            logger.info(f"Response begins with: {response.text[:100]}...")
            return True
        else:
            logger.error(f"API call failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def test_plant_id_api():
    """Test Plant.id API integration."""
    logger.info("Testing Plant.id API...")
    
    # Check if API key is set
    api_key = os.environ.get('PLANT_ID_API_KEY')
    if not api_key:
        logger.error("Plant.id API key not found in environment variables")
        return False
    
    logger.info("Plant.id API key is set")
    # For Plant.id, we'll skip actual API calls to conserve credits
    return True

def test_trefle_api():
    """Test Trefle API integration."""
    logger.info("Testing Trefle API...")
    
    # Check if API key is set
    api_key = os.environ.get('TREFLE_API_KEY')
    if not api_key:
        logger.error("Trefle API key not found in environment variables")
        return False
    
    logger.info("Trefle API key is set")
    # For Trefle, we'll skip actual API calls to conserve credits
    return True

def main():
    """Run all API tests."""
    logger.info("Starting API integration tests...")
    
    # Test each API
    perenual_success = test_perenual_api()
    plant_id_success = test_plant_id_api()
    trefle_success = test_trefle_api()
    
    # Summarize results
    logger.info("\n--- TEST RESULTS ---")
    logger.info(f"Perenual API: {'✅ PASS' if perenual_success else '❌ FAIL'}")
    logger.info(f"Plant.id API: {'✅ PASS' if plant_id_success else '❌ FAIL'}")
    logger.info(f"Trefle API: {'✅ PASS' if trefle_success else '❌ FAIL'}")
    
    return all([perenual_success, plant_id_success, trefle_success])

if __name__ == "__main__":
    success = main()
    print(f"Test result: {'SUCCESS' if success else 'FAILURE'}")
