"""Utility for merging plant data from multiple API sources."""

import logging
from api import (
    get_perenual_plant_details, 
    get_trefle_plant_details,
    get_care_guide, 
    get_growth_data,
    map_plant_to_model,
    map_care_to_model,
    map_growth_data_to_model
)
import crud

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def merge_plant_data(scientific_name, perenual_id=None, trefle_id=None):
    """
    Merge plant data from multiple API sources.
    
    Args:
        scientific_name: Scientific name of the plant
        perenual_id: ID of the plant in Perenual API (optional)
        trefle_id: ID of the plant in Trefle API (optional)
    
    Returns:
        Tuple of (plant_data, care_data) where:
        - plant_data: Merged plant information ready for Plant model
        - care_data: Merged care information ready for PlantCareDetails model
    """
    logger.info(f"Merging data for plant: {scientific_name}")
    
    # Initialize merged data structures
    merged_plant_data = {
        'scientific_name': scientific_name,
        'data_sources': []
    }
    merged_care_data = {}
    
    # Get and merge data from Perenual API if ID provided
    if perenual_id:
        logger.info(f"Fetching Perenual data for ID: {perenual_id}")
        perenual_plant_data = get_perenual_plant_details(perenual_id)
        
        if 'error' not in perenual_plant_data:
            # Map Perenual plant data to model structure
            plant_data = map_plant_to_model(perenual_plant_data)
            merged_plant_data.update(plant_data)
            merged_plant_data['data_sources'].append('perenual')
            
            # Get and map care guide data
            perenual_care_data = get_care_guide(perenual_id)
            care_data = map_care_to_model(perenual_care_data)
            merged_care_data.update(care_data)
        else:
            logger.warning(f"Error fetching Perenual data: {perenual_plant_data.get('error')}")
    
    # Get and merge data from Trefle API if ID provided
    if trefle_id:
        logger.info(f"Fetching Trefle data for ID: {trefle_id}")
        trefle_plant_data = get_trefle_plant_details(trefle_id)
        
        if 'error' not in trefle_plant_data and 'data' in trefle_plant_data:
            plant_data = trefle_plant_data['data']
            
            # Update merged plant data with Trefle data
            if 'common_name' not in merged_plant_data or not merged_plant_data['common_name']:
                merged_plant_data['common_name'] = plant_data.get('common_name')
            
            # Add to data sources
            merged_plant_data['data_sources'].append('trefle')
            
            # Get and map growth data
            growth_data = get_growth_data(trefle_id)
            if 'error' not in growth_data:
                care_data = map_growth_data_to_model(growth_data)
                
                # Selectively update merged care data
                for key, value in care_data.items():
                    if key not in merged_care_data or not merged_care_data[key]:
                        merged_care_data[key] = value
        else:
            logger.warning(f"Error fetching Trefle data: {trefle_plant_data.get('error')}")
    
    return merged_plant_data, merged_care_data

def find_or_create_plant(scientific_name, perenual_id=None, trefle_id=None):
    """
    Find a plant by scientific name or create it by merging data from APIs.
    
    Args:
        scientific_name: Scientific name of the plant
        perenual_id: ID of the plant in Perenual API (optional)
        trefle_id: ID of the plant in Trefle API (optional)
    
    Returns:
        Plant model instance
    """
    # Look for existing plant
    existing_plant = crud.get_plant_by_scientific_name(scientific_name)
    
    if existing_plant:
        logger.info(f"Found existing plant: {scientific_name}")
        return existing_plant
    
    # If not found, merge data and create new plant
    plant_data, care_data = merge_plant_data(scientific_name, perenual_id, trefle_id)
    
    # Create plant in database
    plant = crud.create_plant(**plant_data)
    logger.info(f"Created new plant: {scientific_name} (ID: {plant.plant_id})")
    
    # Create plant care details
    if care_data:
        care_details = crud.create_plant_care_details(plant_id=plant.plant_id, **care_data)
        logger.info(f"Added care details for plant ID: {plant.plant_id}")
    
    return plant

def update_plant_from_apis(plant_id, perenual_id=None, trefle_id=None):
    """
    Update an existing plant with data from APIs.
    
    Args:
        plant_id: ID of the plant in the database
        perenual_id: ID of the plant in Perenual API (optional)
        trefle_id: ID of the plant in Trefle API (optional)
    
    Returns:
        Updated Plant model instance
    """
    # Get existing plant
    plant = crud.get_plant_by_id(plant_id)
    
    if not plant:
        logger.error(f"Plant not found with ID: {plant_id}")
        return None
    
    # Merge data from APIs
    plant_data, care_data = merge_plant_data(
        plant.scientific_name, 
        perenual_id, 
        trefle_id
    )
    
    # Update plant data
    for key, value in plant_data.items():
        if key != 'scientific_name' and value:  # Don't update scientific name
            setattr(plant, key, value)
    
    # Update care details if they exist
    if care_data:
        care_details = crud.get_care_details_by_plant_id(plant_id)
        
        if care_details:
            # Update existing care details
            for key, value in care_data.items():
                if value:  # Only update if value is not None or empty
                    setattr(care_details, key, value)
        else:
            # Create new care details
            care_details = crud.create_plant_care_details(plant_id=plant_id, **care_data)
    
    # Save changes
    crud.db.session.commit()
    logger.info(f"Updated plant: {plant.scientific_name} (ID: {plant.plant_id})")
    
    return plant