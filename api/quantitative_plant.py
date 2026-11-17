"""Client for the Trefle plant API (https://trefle.io), Rootly's only plant API.

Every call goes through _get(), which:
- reads TREFLE_API_KEY from your .env each time (so you never paste the key in code)
- keeps to Trefle's limit of 60 requests per minute by waiting when needed
- if Trefle still answers 429 "Too Many Requests", waits as long as its
  Retry-After header says and tries again (up to twice)
- returns {"error": "..."} instead of crashing when something goes wrong
"""

import logging
import os
import threading
import time
from collections import deque

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

BASE_URL = 'https://trefle.io/api/v1'

# Seconds to wait for Trefle before giving up, so a slow API can't freeze a page
REQUEST_TIMEOUT = 10

# Trefle allows 60 requests per minute per key
MAX_REQUESTS_PER_MINUTE = 60
WINDOW_SECONDS = 60

# How many times to retry after a 429 "Too Many Requests" answer
MAX_RETRIES = 2
# Longest we'll wait before a retry, in seconds
MAX_RETRY_WAIT = 30

_recent_requests = deque()  # times of the requests sent in the last minute
_blocked_until = 0.0         # time.time() before which Trefle said we're out of quota
_lock = threading.Lock()


def get_api_key():
    """Return the Trefle key from the environment (.env), or None."""
    return os.environ.get('TREFLE_API_KEY') or None


def _wait_for_rate_limit():
    """Pause until sending one more request keeps us under 60 per minute."""
    with _lock:
        # Trefle told us earlier that this minute's quota is used up
        if _blocked_until > time.time():
            wait = min(_blocked_until - time.time(), MAX_RETRY_WAIT)
            logger.info(f"Trefle quota used up, waiting {wait:.1f}s for it to reset")
            time.sleep(wait)

        now = time.monotonic()
        # Forget requests older than one minute
        while _recent_requests and now - _recent_requests[0] >= WINDOW_SECONDS:
            _recent_requests.popleft()

        if len(_recent_requests) >= MAX_REQUESTS_PER_MINUTE:
            wait = WINDOW_SECONDS - (now - _recent_requests[0])
            logger.info(f"Trefle limit reached, waiting {wait:.1f}s")
            time.sleep(wait)
            now = time.monotonic()
            _recent_requests.popleft()

        _recent_requests.append(now)


def _note_remaining(response):
    """Remember when Trefle says we have no requests left this minute.

    Trefle sends RateLimit-Remaining and RateLimit-Reset (a unix time) on every
    answer. This matters when another program or a second copy of the app
    shares the same key, since our own counter can't see their requests.
    """
    global _blocked_until
    try:
        remaining = int(response.headers.get('RateLimit-Remaining', ''))
        reset_at = float(response.headers.get('RateLimit-Reset', ''))
    except ValueError:
        return
    if remaining <= 0:
        with _lock:
            _blocked_until = reset_at


def _retry_wait(response, attempt):
    """Seconds to wait after a 429: Trefle's Retry-After header, or 2, 4, 8..."""
    try:
        wait = float(response.headers.get('Retry-After', ''))
    except ValueError:
        wait = 2 ** (attempt + 1)
    return min(max(wait, 0), MAX_RETRY_WAIT)


def _get(path, **params):
    """Send one GET request to Trefle and return the JSON answer."""
    api_key = get_api_key()
    if not api_key:
        logger.error("TREFLE_API_KEY is not set in .env")
        return {"error": "API key not configured"}

    params['token'] = api_key
    try:
        for attempt in range(MAX_RETRIES + 1):
            _wait_for_rate_limit()
            response = requests.get(f"{BASE_URL}{path}", params=params,
                                    timeout=REQUEST_TIMEOUT)
            if response.status_code == 429 and attempt < MAX_RETRIES:
                wait = _retry_wait(response, attempt)
                logger.warning(f"Trefle said too many requests, retrying in {wait:.0f}s")
                time.sleep(wait)
                continue
            response.raise_for_status()
            _note_remaining(response)
            return response.json()
    except requests.exceptions.RequestException as e:
        # Log the error type only: the full message contains the URL with the key
        logger.error(f"Trefle request to {path} failed: {type(e).__name__}")
        return {"error": f"Trefle request failed ({type(e).__name__})"}


def get_plant_list(page=1, limit=20):
    """Get one page of plants from Trefle."""
    return _get('/plants', page=page, limit=limit)


def get_plant_details(plant_id):
    """Get everything Trefle knows about one plant."""
    return _get(f'/plants/{plant_id}')


def search_plants(query, page=1):
    """Search Trefle plants by common or scientific name."""
    return _get('/plants/search', q=query, page=page)


def get_growth_data(plant_id, plant_details=None):
    """Return the growing conditions for a plant.

    Pass plant_details if you already fetched them, to save a request.
    """
    plant_data = plant_details or get_plant_details(plant_id)

    if 'error' in plant_data:
        return plant_data
    data = plant_data.get('data')
    if not data:
        return {"error": "No data found"}

    species = data.get('main_species') or {}
    growth_data = {}

    specs = species.get('specifications') or {}
    growth_data.update({
        'average_height_cm': (specs.get('average_height') or {}).get('cm'),
        'maximum_height_cm': (specs.get('maximum_height') or {}).get('cm'),
        'growth_rate': specs.get('growth_rate'),
        'growth_habit': specs.get('growth_habit'),
        'growth_form': specs.get('growth_form'),
    })

    growth = species.get('growth') or {}
    growth_data.update({
        'growth_months': growth.get('growth_months'),
        'bloom_months': growth.get('bloom_months'),
        'fruit_months': growth.get('fruit_months'),
        'ph_minimum': growth.get('ph_minimum'),
        'ph_maximum': growth.get('ph_maximum'),
        'light': growth.get('light'),
        'atmospheric_humidity': growth.get('atmospheric_humidity'),
        'soil_nutriments': growth.get('soil_nutriments'),
        'soil_salinity': growth.get('soil_salinity'),
        'temperature_minimum_deg_c': (growth.get('minimum_temperature') or {}).get('deg_c'),
        'temperature_maximum_deg_c': (growth.get('maximum_temperature') or {}).get('deg_c'),
    })

    return growth_data


def map_growth_data_to_model(growth_data):
    """Turn Trefle growth data into fields for our PlantCareDetails table."""
    if not growth_data or 'error' in growth_data:
        return {}

    # Trefle rates light from 1 (deep shade) to 9 (full sun), based on where
    # the plant grows wild in Europe. It's often missing for tropical houseplants.
    light_level = growth_data.get('light')
    if light_level is None:
        sunlight_requirements = []
    elif light_level <= 3:
        sunlight_requirements = ["Shade"]
    elif light_level <= 6:
        sunlight_requirements = ["Partial sun"]
    else:
        sunlight_requirements = ["Full sun"]

    min_temp = growth_data.get('temperature_minimum_deg_c')
    max_temp = growth_data.get('temperature_maximum_deg_c')
    temperature_range = (f"{min_temp}°C to {max_temp}°C"
                         if min_temp is not None and max_temp is not None else None)

    growth_rate = growth_data.get('growth_rate')
    difficulty_level = {
        'high': 'Easy', 'rapid': 'Easy',
        'moderate': 'Intermediate',
        'low': 'Difficult', 'slow': 'Difficult',
    }.get((growth_rate or '').lower())

    care_details = {
        'sunlight_requirements': sunlight_requirements,
        'temperature_range': temperature_range,
        'difficulty_level': difficulty_level,
        'growth_rate': growth_rate,
        'pruning_months': growth_data.get('bloom_months') or [],
    }

    ph_min = growth_data.get('ph_minimum')
    ph_max = growth_data.get('ph_maximum')
    if ph_min is not None and ph_max is not None:
        if ph_min < 6.0:
            care_details['soil_preferences'] = 'Acidic soil (pH < 6.0)'
        elif ph_min >= 7.0:
            care_details['soil_preferences'] = 'Alkaline soil (pH > 7.0)'
        else:
            care_details['soil_preferences'] = 'Neutral soil (pH 6.0-7.0)'

    return care_details


def map_plant_to_model(plant):
    """Turn one plant from a Trefle list or search result into Plant fields."""
    return {
        'scientific_name': plant.get('scientific_name') or 'Unknown',
        'common_name': plant.get('common_name'),
        'image_url': plant.get('image_url'),
        'description': (f"A plant in the {plant['family']} family."
                        if plant.get('family') else None),
        'data_sources': ['trefle'],
    }
