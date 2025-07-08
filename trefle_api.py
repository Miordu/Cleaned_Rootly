 # trefle_api.py - Trefle API integration for Rootly
import requests
import os
from typing import Dict, List, Optional
from datetime import datetime

class TrefleAPI:
    """Service class for interacting with the Trefle API."""
    
    def __init__(self, api_token: str = None):
        self.base_url = "https://trefle.io/api/v1"
        self.api_token = api_token or os.getenv('TREFLE_API_TOKEN')
        self.session = requests.Session()
        
        if not self.api_token:
            raise ValueError("Trefle API token is required. Set TREFLE_API_TOKEN environment variable.")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the Trefle API."""
        if params is None:
            params = {}
        
        params['token'] = self.api_token
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to Trefle API: {e}")
            return None
    
    def search_plants(self, query: str, page: int = 1, filter_by: str = None) -> Dict:
        """Search for plants by name."""
        params = {
            'q': query,
            'page': page
        }
        
        if filter_by:
            # Can filter by common_name, scientific_name, family, genus
            params[f'filter[{filter_by}]'] = query
            params.pop('q')  # Remove general query when using specific filter
        
        return self._make_request('/plants', params)
    
    def get_plant_by_id(self, plant_id: int) -> Dict:
        """Get detailed information about a specific plant."""
        return self._make_request(f'/plants/{plant_id}')
    
    def get_plant_species(self, plant_id: int) -> Dict:
        """Get all species for a plant."""
        return self._make_request(f'/plants/{plant_id}/species')
    
    def search_by_scientific_name(self, scientific_name: str) -> Dict:
        """Search for plants by exact scientific name."""
        return self.search_plants(scientific_name, filter_by='scientific_name')
    
    def search_by_common_name(self, common_name: str) -> Dict:
        """Search for plants by common name."""
        return self.search_plants(common_name, filter_by='common_name')
    
    def browse_families(self, page: int = 1) -> Dict:
        """Browse plant families."""
        return self._make_request('/families', {'page': page})
    
    def browse_genus(self, page: int = 1) -> Dict:
        """Browse plant genera."""
        return self._make_request('/genus', {'page': page})
    
    def get_species_details(self, species_id: int) -> Dict:
        """Get detailed information about a species."""
        return self._make_request(f'/species/{species_id}')


# plant_service.py - Service for managing plant data
from model import Plant, PlantCareDetails, db

class PlantService:
    """Service for managing plant data with Trefle API integration."""
    
    def __init__(self, trefle_api: TrefleAPI):
        self.trefle_api = trefle_api
    
    def search_and_create_plants(self, query: str, limit: int = 10) -> List[Plant]:
        """Search Trefle API and create/update plants in database."""
        results = self.trefle_api.search_plants(query)
        
        if not results or 'data' not in results:
            return []
        
        plants = []
        for plant_data in results['data'][:limit]:
            plant = self._create_or_update_plant_from_trefle(plant_data)
            if plant:
                plants.append(plant)
        
        return plants
    
    def _create_or_update_plant_from_trefle(self, trefle_data: Dict) -> Plant:
        """Create or update a plant from Trefle API data."""
        scientific_name = trefle_data.get('scientific_name')
        if not scientific_name:
            return None
        
        # Check if plant already exists
        plant = Plant.query.filter_by(scientific_name=scientific_name).first()
        
        if not plant:
            plant = Plant()
            db.session.add(plant)
        
        # Update plant data
        plant.scientific_name = scientific_name
        plant.common_name = trefle_data.get('common_name')
        plant.plant_type = trefle_data.get('family')  # Using family as plant type
        plant.data_sources = ['trefle']
        plant.last_updated = datetime.utcnow()
        
        # Get detailed information if available
        if 'id' in trefle_data:
            detailed_data = self.trefle_api.get_plant_by_id(trefle_data['id'])
            if detailed_data and 'data' in detailed_data:
                self._update_plant_with_details(plant, detailed_data['data'])
        
        try:
            db.session.commit()
            return plant
        except Exception as e:
            db.session.rollback()
            print(f"Error saving plant {scientific_name}: {e}")
            return None
    
    def _update_plant_with_details(self, plant: Plant, detailed_data: Dict):
        """Update plant with detailed information from Trefle API."""
        # Update basic plant info
        if detailed_data.get('image_url'):
            plant.image_url = detailed_data['image_url']
        
        # Update boolean flags if available in detailed data
        specifications = detailed_data.get('specifications', {})
        if specifications:
            plant.toxic_to_humans = specifications.get('toxicity', {}).get('toxic_to_humans')
            plant.toxic_to_pets = specifications.get('toxicity', {}).get('toxic_to_pets')
            plant.invasive = specifications.get('invasive')
            
            # Growth information
            growth = specifications.get('growth', {})
            if growth:
                if growth.get('atmospheric_humidity'):
                    plant.tropical = growth['atmospheric_humidity'] > 60  # Rough estimate
                
                # Indoor/outdoor based on light requirements
                light = growth.get('light')
                if light:
                    plant.indoor = light <= 6  # Lower light tolerance
                    plant.outdoor = light >= 6  # Higher light needs
        
        # Create or update care details
        if not plant.care_details:
            care_details = PlantCareDetails(plant_id=plant.plant_id)
            db.session.add(care_details)
            plant.care_details = care_details
        
        # Update care details from specifications
        if specifications:
            growth = specifications.get('growth', {})
            if growth:
                # Watering
                if growth.get('soil_humidity'):
                    humidity = growth['soil_humidity']
                    if humidity <= 3:
                        plant.care_details.watering_frequency = "Low - once every 7-10 days"
                        plant.care_details.watering_interval_days = 8
                    elif humidity <= 7:
                        plant.care_details.watering_frequency = "Medium - once every 3-5 days"
                        plant.care_details.watering_interval_days = 4
                    else:
                        plant.care_details.watering_frequency = "High - daily to every other day"
                        plant.care_details.watering_interval_days = 2
                
                # Sunlight
                if growth.get('light'):
                    light = growth['light']
                    if light <= 3:
                        plant.care_details.sunlight_requirements = ['low', 'shade']
                        plant.care_details.sunlight_duration_min = 2
                        plant.care_details.sunlight_duration_max = 4
                    elif light <= 7:
                        plant.care_details.sunlight_requirements = ['partial_sun', 'partial_shade']
                        plant.care_details.sunlight_duration_min = 4
                        plant.care_details.sunlight_duration_max = 6
                    else:
                        plant.care_details.sunlight_requirements = ['full_sun']
                        plant.care_details.sunlight_duration_min = 6
                        plant.care_details.sunlight_duration_max = 8
                
                # Temperature (convert from potential Celsius to descriptive range)
                if growth.get('minimum_temperature'):
                    min_temp = growth['minimum_temperature']
                    if min_temp < 10:
                        plant.care_details.temperature_range = "Cool (10-18°C / 50-65°F)"
                    elif min_temp < 18:
                        plant.care_details.temperature_range = "Moderate (15-24°C / 60-75°F)"
                    else:
                        plant.care_details.temperature_range = "Warm (20-30°C / 70-85°F)"


