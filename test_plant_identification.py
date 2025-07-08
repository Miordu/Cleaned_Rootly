#!/usr/bin/env python3
"""Test script for plant identification functionality."""

import os
import sys
import logging
from dotenv import load_dotenv
from api.plant_id import identify_plant, map_identification_result

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_test_image():
    """Create a simple test image for demonstration purposes."""
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple 200x200 green square to simulate a leaf
        img = Image.new('RGB', (200, 200), color='green')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple leaf-like shape
        draw.ellipse([50, 50, 150, 150], fill='darkgreen', outline='black', width=2)
        draw.line([100, 50, 100, 150], fill='black', width=2)  # Leaf vein
        
        # Save test image
        test_image_path = 'test_plant_image.jpg'
        img.save(test_image_path, 'JPEG')
        logger.info(f"Created test image: {test_image_path}")
        return test_image_path
        
    except ImportError:
        logger.error("PIL/Pillow not available. Cannot create test image.")
        return None
    except Exception as e:
        logger.error(f"Error creating test image: {e}")
        return None

def test_api_keys():
    """Test if API keys are properly configured."""
    logger.info("Testing API key configuration...")
    
    plant_id_key = os.getenv('PLANT_ID_API_KEY')
    plantnet_key = os.getenv('PLANTNET_API_KEY')
    
    if plant_id_key:
        logger.info("✅ Plant.id API key is configured")
    else:
        logger.warning("❌ Plant.id API key not found")
    
    if plantnet_key:
        logger.info("✅ PlantNet API key is configured")
    else:
        logger.warning("❌ PlantNet API key not found")
    
    return bool(plant_id_key or plantnet_key)

def test_api_response_format():
    """Test that the API response format is correctly handled."""
    logger.info("Testing API response format handling...")
    
    # Test with an empty response
    empty_result = map_identification_result({})
    if empty_result is None:
        logger.info("✅ Empty response handled correctly")
        return True
    else:
        logger.error("❌ Empty response not handled correctly")
        return False

def test_live_identification():
    """Test live plant identification with Plant.id API."""
    logger.info("Testing live plant identification...")
    
    # Check if we have API keys
    if not os.getenv('PLANT_ID_API_KEY'):
        logger.warning("⚠️ Skipping live test - no Plant.id API key configured")
        return False
    
    # Create a test image
    test_image_path = create_test_image()
    if not test_image_path:
        logger.error("❌ Could not create test image")
        return False
    
    try:
        # Perform identification
        logger.info("🌱 Calling Plant.id API...")
        result = identify_plant(test_image_path)
        
        if 'error' in result:
            logger.error(f"❌ API call failed: {result['error']}")
            return False
        
        # Map the result
        mapped_result = map_identification_result(result)
        
        if mapped_result:
            logger.info("✅ Live identification successful:")
            logger.info(f"   Scientific name: {mapped_result.get('scientific_name')}")
            logger.info(f"   Common names: {mapped_result.get('common_names')}")
            logger.info(f"   Confidence: {mapped_result.get('confidence_score', 0):.2%}")
            logger.info(f"   API source: {mapped_result.get('api_source')}")
            return True
        else:
            logger.error("❌ Result mapping failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Live identification test failed: {e}")
        return False
    finally:
        # Clean up test image
        if test_image_path and os.path.exists(test_image_path):
            os.remove(test_image_path)
            logger.info("🗑️ Cleaned up test image")

def main():
    """Run all plant identification tests."""
    logger.info("🌿 Starting Plant Identification Tests")
    logger.info("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: API key configuration
    if test_api_keys():
        tests_passed += 1
    
    # Test 2: API response format handling
    if test_api_response_format():
        tests_passed += 1
    
    # Test 3: Live identification (if API keys available)
    if test_live_identification():
        tests_passed += 1
    
    # Summary
    logger.info("=" * 50)
    logger.info(f"🧪 Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests passed! Plant identification is working correctly.")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - tests_passed} test(s) failed. Check configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
