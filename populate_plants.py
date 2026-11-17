#!/usr/bin/env python3
"""
Seed script that fills the database with popular houseplants plus plants from
the Trefle API. Needs TREFLE_API_KEY in .env for the Trefle part.
Uses about 2 Trefle requests, well under the 60-per-minute limit.
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
import crud

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.quantitative_plant import get_plant_list as get_trefle_plants


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
                    common_name=plant_data.get('common_name') or 'Unknown Plant',
                    image_url=plant_data.get('image_url'),
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
        
        # Add plants from Trefle API
        trefle_plants_added = populate_plants_from_trefle()

        
        # Final count
        final_count = Plant.query.count()
        total_added = final_count - existing_count
        
        logger.info(f"Population complete!")
        logger.info(f"Plants added this session: {total_added}")
        logger.info(f"  - Popular houseplants: {houseplants_added}")
        logger.info(f"  - From Trefle API: {trefle_plants_added}")
        logger.info(f"Total plants in database: {final_count}")
        
        if trefle_plants_added == 0:
            logger.warning("No Trefle plants added. Is TREFLE_API_KEY set in .env?")

if __name__ == "__main__":
    main()
