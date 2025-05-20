"""Utility for merging plant data from multiple API sources."""

import logging
import crud

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def merge_plant_data(scientific_name, perenual_id=None, trefle_id=None):
    """
    Merge plant data from multiple API sources.
    Currently using mock data since Perenual API is disabled.
    
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
    
    # Initialize with basic data
    merged_plant_data = {
        'scientific_name': scientific_name,
        'common_name': scientific_name.split(' ')[0],  # Use genus as common name
        'data_sources': ['mock'],
        'description': f"This is a placeholder description for {scientific_name}.",
        'indoor': True,
        'outdoor': True
    }
    
    merged_care_data = {
        'watering_frequency': 'Weekly',
        'sunlight_requirements': ['Bright indirect light'],
        'soil_preferences': 'Well-draining potting mix',
        'difficulty_level': 'Moderate'
    }
    
    # Add Trefle data if ID is provided
    if trefle_id:
        from api.quantitative_plant import get_trefle_plant_details, get_growth_data, map_growth_data_to_model
        
        logger.info(f"Fetching Trefle data for ID: {trefle_id}")
        trefle_plant_data = get_trefle_plant_details(trefle_id)
        
        if 'error' not in trefle_plant_data and 'data' in trefle_plant_data:
            # Update merged data with Trefle data
            merged_plant_data['data_sources'].append('trefle')
            
            # Get and map growth data
            growth_data = get_growth_data(trefle_id)
            if 'error' not in growth_data:
                care_data = map_growth_data_to_model(growth_data)
                
                # Update merged care data
                for key, value in care_data.items():
                    if value:  # Only update if value is not None or empty
                        merged_care_data[key] = value
    
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
