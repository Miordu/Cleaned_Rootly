#!/usr/bin/env python3
"""
Test script for browse plants functionality with real API integration
"""
import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_perenual_api_direct():
    """Test direct Perenual API call"""
    logger.info("🌿 Testing direct Perenual API access...")
    
    api_key = os.getenv('PERENUAL_API_KEY')
    if not api_key:
        logger.error("❌ PERENUAL_API_KEY not found in environment")
        return False
    
    try:
        url = f"https://perenual.com/api/species-list?key={api_key}&page=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API response received with {len(data.get('data', []))} plants")
            
            # Show first plant as example
            if data.get('data'):
                first_plant = data['data'][0]
                logger.info(f"   Example plant: {first_plant.get('common_name', 'Unknown')}")
                logger.info(f"   Scientific: {first_plant.get('scientific_name', ['Unknown'])[0] if first_plant.get('scientific_name') else 'Unknown'}")
                logger.info(f"   Has image: {'Yes' if first_plant.get('default_image') else 'No'}")
            return True
        else:
            logger.error(f"❌ API returned status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ API call failed: {e}")
        return False

def test_flask_browse_route():
    """Test the Flask browse plants route"""
    logger.info("🌐 Testing Flask browse plants route...")
    
    try:
        # Start the Flask server in the background if not running
        response = requests.get('http://127.0.0.1:5000/browse-plants', timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for key elements that indicate API data is being used
            if 'class="plant-card"' in html_content:
                logger.info("✅ Plant cards found in response")
                
                # Count approximate number of plants shown
                plant_count = html_content.count('class="plant-card"')
                logger.info(f"   Found {plant_count} plant cards")
                
                # Check for images
                if 'default_image' in html_content or '.jpg' in html_content or '.png' in html_content:
                    logger.info("✅ Plant images appear to be present")
                else:
                    logger.warning("⚠️ No plant images detected")
                
                return True
            else:
                logger.warning("⚠️ No plant cards found - may be using fallback data")
                return False
        else:
            logger.error(f"❌ Browse route returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Could not connect to Flask server at http://127.0.0.1:5000")
        logger.info("   Make sure the Flask server is running with: python server.py")
        return False
    except Exception as e:
        logger.error(f"❌ Request failed: {e}")
        return False

def test_perenual_module():
    """Test the Perenual API module directly"""
    logger.info("🔌 Testing Perenual API module...")
    
    try:
        # Add current directory to path to import our modules
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from api.perenual import get_plant_list, get_plant_details
        
        # Test get_plant_list
        plants = get_plant_list(page=1, size=5)
        if plants:
            logger.info(f"✅ get_plant_list() returned {len(plants)} plants")
            
            # Test plant details for first plant
            if plants[0].get('id'):
                plant_id = plants[0]['id']
                details = get_plant_details(plant_id)
                if details:
                    logger.info(f"✅ get_plant_details({plant_id}) successful")
                    logger.info(f"   Plant: {details.get('common_name', 'Unknown')}")
                else:
                    logger.warning(f"⚠️ get_plant_details({plant_id}) returned no data")
            
            return True
        else:
            logger.error("❌ get_plants() returned no data")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Could not import Perenual API module: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Perenual module test failed: {e}")
        return False

def main():
    """Run all browse plants tests"""
    logger.info("🌿 Starting Browse Plants Tests")
    logger.info("=" * 50)
    
    tests = [
        ("API Key Configuration", test_perenual_api_direct),
        ("Perenual API Module", test_perenual_module),
        ("Flask Browse Route", test_flask_browse_route),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"Testing {test_name}...")
        if test_func():
            passed += 1
        logger.info("")
    
    logger.info("=" * 50)
    logger.info(f"🧪 Tests completed: {passed}/{total} passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Browse plants functionality is working correctly.")
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
