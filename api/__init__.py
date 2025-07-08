"""API integration package for Rootly."""

# Import API modules for easier access
from api.perenual import (
    get_plant_list as get_perenual_plant_list,
    get_plant_details as get_perenual_plant_details,
    search_plants as search_perenual_plants,
    get_care_guide,
    map_plant_to_model,
    map_care_to_model
)

from api.plant_id import (
    identify_plant,
    identify_plant_from_binary,
    map_identification_result
)

from api.plant_health import (
    assess_health,
    assess_health_from_binary,
    map_health_assessment
)

from api.quantitative_plant import (
    get_plant_list as get_trefle_plant_list,
    get_plant_details as get_trefle_plant_details,
    search_plants as search_trefle_plants,
    get_growth_data,
    map_growth_data_to_model
)

# Version information
__version__ = '0.1.0'
