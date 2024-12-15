import logging
from typing import Dict, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.distance import geodesic
from ..config import Config

logger = logging.getLogger(__name__)

# Initialize geocoder with custom user agent
geocoder = Nominatim(user_agent="infocal_app")

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude values"""
    try:
        lat = float(lat)
        lon = float(lon)
        
        if not (-90 <= lat <= 90):
            logger.error(f"Invalid latitude: {lat}")
            return False
        if not (-180 <= lon <= 180):
            logger.error(f"Invalid longitude: {lon}")
            return False
            
        return True
    except (TypeError, ValueError) as e:
        logger.error(f"Error validating coordinates: {str(e)}")
        return False

def geocode_location(location_name: str) -> Dict:
    """
    Convert a location name to coordinates and structured data.
    
    Args:
        location_name (str): Name of the location to geocode
        
    Returns:
        dict: Location data including coordinates and formatted address
        
    Raises:
        ValueError: If location cannot be geocoded
    """
    try:
        logger.info(f"Geocoding location: {location_name}")
        
        # Add a retry mechanism
        max_retries = 3
        location = None
        
        for attempt in range(max_retries):
            try:
                location = geocoder.geocode(
                    location_name,
                    exactly_one=True,
                    language='en',
                    timeout=10
                )
                if location:
                    break
            except GeocoderTimedOut:
                if attempt == max_retries - 1:
                    raise
                continue
        
        if location is None:
            raise ValueError(f"Could not find coordinates for location: {location_name}")
            
        # Validate coordinates
        if not validate_coordinates(location.latitude, location.longitude):
            raise ValueError(f"Invalid coordinates returned for location: {location_name}")
            
        location_data = {
            'name': location_name,
            'lat': location.latitude,
            'lon': location.longitude,
            'address': location.address,
            'raw': {
                key: value 
                for key, value in location.raw.items() 
                if key in ['place_id', 'osm_type', 'osm_id', 'type', 'class']
            }
        }
        
        logger.info(f"Successfully geocoded location: {location_name}")
        return location_data
        
    except GeocoderTimedOut as e:
        logger.error(f"Geocoding timeout for {location_name}: {str(e)}")
        raise ValueError("Geocoding service timed out. Please try again.")
    except GeocoderServiceError as e:
        logger.error(f"Geocoding service error for {location_name}: {str(e)}")
        raise ValueError("Geocoding service is currently unavailable. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error geocoding {location_name}: {str(e)}")
        raise ValueError(f"Unable to find location: {str(e)}")

def check_location_relevance(user_location: Dict, warning_location: Dict) -> bool:
    """
    Check if a warning location is relevant for a user location based on distance.
    
    Args:
        user_location (Dict): User's location with lat/lon
        warning_location (Dict): Warning's location with lat/lon
        
    Returns:
        bool: True if warning is relevant
    """
    try:
        # Log input values
        logger.debug(f"Checking relevance - User location: {user_location}")
        logger.debug(f"Checking relevance - Warning location: {warning_location}")

        # Extract coordinates
        user_lat = float(user_location.get('lat', 0))
        user_lon = float(user_location.get('lon', 0))
        warn_lat = float(warning_location.get('lat', 0))
        warn_lon = float(warning_location.get('lon', 0))

        # Log extracted coordinates
        logger.debug(f"User coordinates: ({user_lat}, {user_lon})")
        logger.debug(f"Warning coordinates: ({warn_lat}, {warn_lon})")

        # Validate coordinates
        if not all([
            -90 <= lat <= 90 and -180 <= lon <= 180
            for lat, lon in [(user_lat, user_lon), (warn_lat, warn_lon)]
        ]):
            logger.error(f"Invalid coordinates detected:")
            logger.error(f"User: ({user_lat}, {user_lon})")
            logger.error(f"Warning: ({warn_lat}, {warn_lon})")
            return False

        # Calculate distance
        from geopy.distance import geodesic
        user_coords = (user_lat, user_lon)
        warn_coords = (warn_lat, warn_lon)
        
        distance = geodesic(user_coords, warn_coords).kilometers
        is_relevant = distance <= Config.WARNING_RADIUS_KM
        
        logger.debug(
            f"Distance between points: {distance:.2f}km, "
            f"Radius: {Config.WARNING_RADIUS_KM}km, "
            f"Is relevant: {is_relevant}"
        )
        
        return is_relevant
        
    except Exception as e:
        logger.error(f"Error checking location relevance: {str(e)}", exc_info=True)
        return False

def get_bounding_box(lat: float, lon: float, radius_km: float) -> Dict:
    """Calculate a bounding box around a point"""
    try:
        from math import radians, degrees, cos, sin, asin, sqrt
        
        # Convert radius from kilometers to degrees
        r = radius_km / 111.321  # 1 degree = 111.321 km
        
        # Calculate the bounding box
        min_lat = max(-90, lat - r)
        max_lat = min(90, lat + r)
        
        # Adjust longitude range based on latitude to account for earth's curvature
        r_lon = r / cos(radians(lat))
        min_lon = max(-180, lon - r_lon)
        max_lon = min(180, lon + r_lon)
        
        return {
            'min_lat': min_lat,
            'max_lat': max_lat,
            'min_lon': min_lon,
            'max_lon': max_lon
        }
        
    except Exception as e:
        logger.error(f"Error calculating bounding box: {str(e)}")
        raise ValueError(f"Could not calculate bounding box: {str(e)}")
