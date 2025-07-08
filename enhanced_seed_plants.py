import os
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from server import app
from model import db, Plant, PlantCareDetails
from api.perenual import get_plant_list, get_plant_details
from api.quantitative_plant import get_plant_list as get_trefle_list, get_plant_details as get_trefle_details, map_growth_data_to_model

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def map_perenual_plant_to_model(plant_data):
    """Map Perenual API data to model structure."""
    # Handle scientific name array format
    scientific_name = plant_data.get('scientific_name', [])
    if isinstance(scientific_name, list):
        scientific_name = scientific_name[0] if scientific_name else 'Unknown'
    
    # Get image URL
    image_url = None
    if plant_data.get('default_image'):
        image_url = plant_data['default_image'].get('original_url')
    
    return {
        'scientific_name': scientific_name,
        'common_name': plant_data.get('common_name', 'Unknown Plant'),
        'description': plant_data.get('description', 'No description available.'),
        'image_url': image_url,
        'indoor': plant_data.get('indoor', False),
        'outdoor': plant_data.get('outdoor', False),
        'tropical': plant_data.get('tropical', False),
        'poisonous_to_humans': plant_data.get('poisonous_to_humans', False),
        'poisonous_to_pets': plant_data.get('poisonous_to_pets', False),
        'invasive': plant_data.get('invasive', False),
        'rare': plant_data.get('rare', False),
        'data_sources': ['perenual'],
        'last_updated': datetime.utcnow()
    }


def map_trefle_plant_to_model(plant_data):
    """Map Trefle API data to model structure."""
    # Get image URL from Trefle data
    image_url = None
    if plant_data.get('image_url'):
        image_url = plant_data['image_url']
    elif plant_data.get('images') and plant_data['images']:
        image_url = plant_data['images'][0].get('url')
    
    return {
        'scientific_name': plant_data.get('scientific_name', 'Unknown'),
        'common_name': plant_data.get('common_name', 'Unknown Plant'),
        'description': plant_data.get('description', 'No description available.'),
        'image_url': image_url,
        'indoor': plant_data.get('indoor', False),
        'outdoor': plant_data.get('outdoor', True),
        'tropical': plant_data.get('tropical', False),
        'data_sources': ['trefle'],
        'last_updated': datetime.utcnow()
    }


def seed_database(per_page=30, max_plants=2000):
    """Seed the database with plant data from multiple APIs."""
    logger.info(f"Starting to seed database with up to {max_plants} plants...")
    
    added_count = 0
    page = 1
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    while added_count < max_plants and consecutive_errors < max_consecutive_errors:
        try:
            # Fetch plants from Perenual API
            logger.info(f"Fetching plants from Perenual API, page {page}...")
            perenual_data = get_plant_list(page=page, size=per_page)
            
            if perenual_data.get('data'):
                consecutive_errors = 0  # Reset error count on successful fetch
                
                for plant_data in perenual_data.get('data', []):
                    try:
                        model_data = map_perenual_plant_to_model(plant_data)
                        
                        # Only add plants with images
                        if model_data.get('image_url'):
                            # Check if plant already exists
                            existing_plant = Plant.query.filter_by(
                                scientific_name=model_data['scientific_name']
                            ).first()
                            
                            if not existing_plant:
                                plant = Plant(**model_data)
                                db.session.add(plant)
                                added_count += 1
                                logger.info(f"Added plant: {model_data['common_name']} ({model_data['scientific_name']})")
                                
                                if added_count >= max_plants:
                                    break
                    except Exception as e:
                        logger.error(f"Error processing Perenual plant: {e}")
                        continue
            else:
                consecutive_errors += 1
                logger.warning(f"No data from Perenual API, consecutive errors: {consecutive_errors}")
            
            # Break if we've reached the target
            if added_count >= max_plants:
                break
            
            # Fetch additional data from Trefle API
            logger.info(f"Fetching plants from Trefle API, page {page}...")
            trefle_data = get_trefle_list(page=page, limit=per_page)
            
            if trefle_data.get('data'):
                for trefle_plant in trefle_data.get('data', []):
                    try:
                        model_data = map_trefle_plant_to_model(trefle_plant)
                        
                        # Only add plants with images
                        if model_data.get('image_url'):
                            # Check if plant already exists
                            existing_plant = Plant.query.filter_by(
                                scientific_name=model_data['scientific_name']
                            ).first()
                            
                            if not existing_plant:
                                plant = Plant(**model_data)
                                db.session.add(plant)
                                added_count += 1
                                logger.info(f"Added plant: {model_data['common_name']} ({model_data['scientific_name']})")
                                
                                if added_count >= max_plants:
                                    break
                    except Exception as e:
                        logger.error(f"Error processing Trefle plant: {e}")
                        continue
            
            # Commit every 50 plants to avoid losing progress
            if added_count % 50 == 0:
                db.session.commit()
                logger.info(f"Committed {added_count} plants to database")
            
            page += 1
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error on page {page}: {e}")
            consecutive_errors += 1
            time.sleep(2)  # Wait longer on errors
    
    # Final commit
    db.session.commit()
    logger.info(f"Seeding complete! Added {added_count} plants to the database.")
    
    # Check final count
    total_plants = Plant.query.count()
    logger.info(f"Total plants in database: {total_plants}")


if __name__ == "__main__":
    with app.app_context():
        seed_database()
