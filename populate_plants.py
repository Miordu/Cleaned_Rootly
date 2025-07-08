#!/usr/bin/env python3
"""
Enhanced seed script to populate the database with 100+ plants from various APIs
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app
from model import db, Plant, PlantCareDetails, Region
from api.perenual import get_plant_list, get_plant_details, map_plant_to_model
import crud

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.quantitative_plant import get_plant_list as get_trefle_plants
from api.plant_image_apis import PlantImageFetcher


def create_regions():
    """Create basic regions if they don't exist."""
    regions = [
        {'name': 'North America', 'climate_zone': 'Temperate', 'avg_temperature': 20.0, 'humidity_level': 'Moderate'},
        {'name': 'Europe', 'climate_zone': 'Temperate', 'avg_temperature': 15.0, 'humidity_level': 'Moderate'},
        {'name': 'Asia', 'climate_zone': 'Varied', 'avg_temperature': 25.0, 'humidity_level': 'High'},
        {'name': 'South America', 'climate_zone': 'Tropical', 'avg_temperature': 28.0, 'humidity_level': 'High'},
        {'name': 'Africa', 'climate_zone': 'Tropical', 'avg_temperature': 30.0, 'humidity_level': 'Low'},
        {'name': 'Australia', 'climate_zone': 'Arid', 'avg_temperature': 25.0, 'humidity_level': 'Low'},
    ]
    
    for region_data in regions:
        existing_region = Region.query.filter_by(name=region_data['name']).first()
        if not existing_region:
            region = Region(**region_data)
            db.session.add(region)
    
    db.session.commit()
    logger.info("Regions created successfully")

def populate_plants_from_image_apis():
    """Populate database with plants from image APIs."""
    logger.info("Starting to populate plants from image APIs...")
    
    plants_added = 0
    target_plants = 25  # set based on initial targets

    # Initialize PlantImageFetcher
    image_fetcher = PlantImageFetcher(
        trefle_key=os.getenv('TREFLE_API_KEY'),
        perenual_key=os.getenv('PERENUAL_API_KEY')
    )
    sample_queries = ['fern', 'rose', 'oak', 'cactus', 'ivy']  # Sample searches
    
    for query in sample_queries:
        try:
            image_url = image_fetcher.get_best_image(query)
            if not image_url:
                logger.warning(f"No image found for {query}")
                continue
            
            existing_plant = Plant.query.filter_by(common_name=query).first()
            if existing_plant:
                continue
            
            plant = Plant(
                scientific_name='N/A',
                common_name=query,
                image_url=image_url,
                data_sources=['image_api'],
                last_updated=datetime.utcnow()
            )
            db.session.add(plant)
            plants_added += 1
            
            if plants_added % 5 == 0:
                logger.info(f"Added {plants_added} plants from image APIs so far...")
            
            if plants_added >= target_plants:
                break
                
        except Exception as e:
            logger.error(f"Error processing plant {query} from image APIs: {e}")
            continue
    
    db.session.commit()
    logger.info(f"Successfully added {plants_added} plants from image APIs")
    return plants_added

def populate_plants_from_trefle():
    """Populate database with plants from Trefle API."""
    logger.info("Starting to populate plants from Trefle API...")
    
    plants_added = 0
    target_plants = 50  # Divide the target among the APIs
    
    # Fetch multiple pages
    for page in range(1, 3):  # Adjust page numbers as needed
        logger.info(f"Fetching Trefle page {page}...")
        
        plant_list = get_trefle_plants(page=page, limit=25)  # 'limit' used instead of 'size'
        
        if not plant_list or 'data' not in plant_list:
            logger.warning(f"No data returned for Trefle page {page}")
            continue
        
        for plant_data in plant_list['data']:
            try:
                # Check if plant already exists by scientific_name
                existing_plant = Plant.query.filter_by(
                    scientific_name=plant_data.get('scientific_name', f"Unknown_{plant_data.get('id', 'N/A')}")
                ).first()
                
                if existing_plant:
                    continue
                
                # Create new plant record
                plant = Plant(
                    scientific_name=plant_data.get('scientific_name', f"Unknown_{plant_data.get('id', 'N/A')}"),
                    common_name=plant_data.get('common_name', 'Unknown Plant'),
                    description=plant_data.get('family_common_name', '') or f"A plant in the {plant_data.get('family', 'plant')} family.",
                    data_sources=['trefle'],
                    last_updated=datetime.utcnow()
                )
                
                db.session.add(plant)
                db.session.flush()  # Get the plant ID
                
                # Try to get detailed care information if available
                # Care details logic here if applicable
                
                plants_added += 1
                
                if plants_added % 10 == 0:
                    logger.info(f"Added {plants_added} Trefle plants so far...")
                
                if plants_added >= target_plants:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing Trefle plant {plant_data.get('common_name', 'Unknown')}: {e}")
                continue
        
        if plants_added >= target_plants:
            break
    
    db.session.commit()
    logger.info(f"Successfully added {plants_added} Trefle plants")
    return plants_added

def populate_plants_from_perenual():
    """Populate database with plants from Perenual API."""
    logger.info("Starting to populate plants from Perenual API...")
    
    plants_added = 0
    target_plants = 50  # Divide the target among the APIs
    
    # Fetch multiple pages to get enough plants
    for page in range(1, 6):  # Pages 1-5 (should give us 100+ plants)
        logger.info(f"Fetching page {page}...")
        
        plant_list = get_plant_list(page=page, size=20)
        
        if not plant_list or 'data' not in plant_list:
            logger.warning(f"No data returned for page {page}")
            continue
        
        for plant_data in plant_list['data']:
            try:
                # Extract scientific name - handle both string and array formats
                scientific_name = plant_data.get('scientific_name', f"Unknown_{plant_data.get('id', 'N/A')}")
                if isinstance(scientific_name, list):
                    scientific_name = scientific_name[0] if scientific_name else f"Unknown_{plant_data.get('id', 'N/A')}"
                
                # Check if plant already exists
                existing_plant = Plant.query.filter_by(
                    scientific_name=scientific_name
                ).first()
                
                if existing_plant:
                    continue
                
                # Create new plant record
                plant = Plant(
                    scientific_name=scientific_name,
                    common_name=plant_data.get('common_name', 'Unknown Plant'),
                    description=plant_data.get('description', 'A beautiful plant from our database.'),
                    image_url=plant_data.get('default_image', {}).get('original_url') if plant_data.get('default_image') else None,
                    indoor=plant_data.get('indoor', False),
                    outdoor=not plant_data.get('indoor', True),
                    tropical=plant_data.get('tropical', False),
                    poisonous_to_humans=plant_data.get('poisonous_to_humans', False),
                    poisonous_to_pets=plant_data.get('poisonous_to_pets', False),
                    data_sources=['perenual'],
                    last_updated=datetime.utcnow()
                )
                
                db.session.add(plant)
                db.session.flush()  # Get the plant ID
                
                # Try to get detailed care information
                try:
                    if plant_data.get('id'):
                        details = get_plant_details(plant_data['id'])
                        if details and isinstance(details, dict):
                            # Create care details
                            care_details = PlantCareDetails(
                                plant_id=plant.plant_id,
                                watering_frequency=details.get('watering', 'Weekly'),
                                sunlight_requirements=details.get('sunlight', ['Medium light']),
                                soil_preferences=details.get('soil', 'Well-draining potting mix'),
                                temperature_range='65-80°F',
                                difficulty_level=details.get('care_level', 'Moderate'),
                                propagation_methods=['Cuttings', 'Seeds']
                            )
                            db.session.add(care_details)
                except Exception as e:
                    logger.warning(f"Could not fetch care details for {plant.common_name}: {e}")
                
                plants_added += 1
                
                if plants_added % 10 == 0:
                    logger.info(f"Added {plants_added} plants so far...")
                
                if plants_added >= target_plants:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing plant {plant_data.get('common_name', 'Unknown')}: {e}")
                continue
        
        if plants_added >= target_plants:
            break
    
    db.session.commit()
    logger.info(f"Successfully added {plants_added} plants from Perenual API")
    return plants_added

def add_popular_houseplants():
    """Add popular houseplants manually to ensure we have good variety."""
    popular_plants = [
        {
            'scientific_name': 'Monstera deliciosa',
            'common_name': 'Swiss Cheese Plant',
            'description': 'A popular houseplant known for its large, split leaves.',
            'indoor': True,
            'outdoor': False,
            'care': {
                'watering_frequency': 'Weekly',
                'sunlight_requirements': ['Bright indirect light'],
                'soil_preferences': 'Well-draining potting mix',
                'difficulty_level': 'Easy'
            }
        },
        {
            'scientific_name': 'Ficus lyrata',
            'common_name': 'Fiddle Leaf Fig',
            'description': 'A trendy houseplant with large, violin-shaped leaves.',
            'indoor': True,
            'outdoor': False,
            'care': {
                'watering_frequency': 'Weekly',
                'sunlight_requirements': ['Bright indirect light'],
                'soil_preferences': 'Well-draining potting mix',
                'difficulty_level': 'Moderate'
            }
        },
        {
            'scientific_name': 'Sansevieria trifasciata',
            'common_name': 'Snake Plant',
            'description': 'A hardy succulent known for its air-purifying qualities.',
            'indoor': True,
            'outdoor': False,
            'care': {
                'watering_frequency': 'Every 2-3 weeks',
                'sunlight_requirements': ['Low to bright light'],
                'soil_preferences': 'Well-draining succulent mix',
                'difficulty_level': 'Easy'
            }
        },
        {
            'scientific_name': 'Pothos aureus',
            'common_name': 'Golden Pothos',
            'description': 'A trailing vine that\'s perfect for beginners.',
            'indoor': True,
            'outdoor': False,
            'care': {
                'watering_frequency': 'Weekly',
                'sunlight_requirements': ['Low to medium light'],
                'soil_preferences': 'Regular potting mix',
                'difficulty_level': 'Easy'
            }
        },
        {
            'scientific_name': 'Spathiphyllum wallisii',
            'common_name': 'Peace Lily',
            'description': 'An elegant flowering houseplant with white blooms.',
            'indoor': True,
            'outdoor': False,
            'care': {
                'watering_frequency': 'Weekly',
                'sunlight_requirements': ['Low to medium light'],
                'soil_preferences': 'Well-draining potting mix',
                'difficulty_level': 'Easy'
            }
        }
    ]
    
    plants_added = 0
    
    for plant_data in popular_plants:
        try:
            # Check if plant already exists
            existing_plant = Plant.query.filter_by(
                scientific_name=plant_data['scientific_name']
            ).first()
            
            if existing_plant:
                continue
            
            # Create new plant record
            plant = Plant(
                scientific_name=plant_data['scientific_name'],
                common_name=plant_data['common_name'],
                description=plant_data['description'],
                indoor=plant_data['indoor'],
                outdoor=plant_data['outdoor'],
                data_sources=['manual'],
                last_updated=datetime.utcnow()
            )
            
            db.session.add(plant)
            db.session.flush()
            
            # Add care details
            care_details = PlantCareDetails(
                plant_id=plant.plant_id,
                watering_frequency=plant_data['care']['watering_frequency'],
                sunlight_requirements=plant_data['care']['sunlight_requirements'],
                soil_preferences=plant_data['care']['soil_preferences'],
                difficulty_level=plant_data['care']['difficulty_level'],
                propagation_methods=['Cuttings', 'Division']
            )
            
            db.session.add(care_details)
            plants_added += 1
            
        except Exception as e:
            logger.error(f"Error adding plant {plant_data['common_name']}: {e}")
    
    db.session.commit()
    logger.info(f"Added {plants_added} popular houseplants")
    return plants_added

def main():
    """Main function to populate the database."""
    logger.info("Starting database population...")
    
    with app.app_context():
        # Create regions first
        create_regions()
        
        # Count existing plants
        existing_count = Plant.query.count()
        logger.info(f"Current plants in database: {existing_count}")
        
        # Add popular houseplants first
        houseplants_added = add_popular_houseplants()
        
        # Add plants from Image APIs
        image_plants_added = populate_plants_from_image_apis()
        
        # Add plants from Trefle API
        trefle_plants_added = populate_plants_from_trefle()
        
        # Add plants from Perenual API
        perenual_plants_added = populate_plants_from_perenual()
        
        # Final count
        final_count = Plant.query.count()
        total_added = final_count - existing_count
        
        logger.info(f"Population complete!")
        logger.info(f"Plants added this session: {total_added}")
        logger.info(f"  - Popular houseplants: {houseplants_added}")
        logger.info(f"  - From Image APIs: {image_plants_added}")
        logger.info(f"  - From Trefle API: {trefle_plants_added}")
        logger.info(f"  - From Perenual API: {perenual_plants_added}")
        logger.info(f"Total plants in database: {final_count}")
        
        if final_count >= 100:
            logger.info("✅ Success! Database now has 100+ plants")
        else:
            logger.warning(f"⚠️ Only {final_count} plants in database. May need more API calls.")

if __name__ == "__main__":
    main()
