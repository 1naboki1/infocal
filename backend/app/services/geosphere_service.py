import logging
import requests
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GeosphereService:
    def __init__(self):
        self.base_url = "https://warnungen.zamg.at/wsapp/api"
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'InfoCal/1.0'
        }
        self.timeout = 10

    def get_warnings(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetch warnings for all provided locations.
        
        Args:
            locations: List of location dictionaries with lat and lon coordinates
            
        Returns:
            List[Dict]: List of processed warnings
        """
        all_warnings = []
        seen_warning_ids = set()

        for location in locations:
            try:
                lat = location.get('lat')
                lon = location.get('lon')
                if lat is None or lon is None:
                    logger.error(f"Missing coordinates for location: {location}")
                    continue

                warnings = self.get_warnings_for_location(lat, lon)
                
                # Deduplicate warnings based on warning_id
                for warning in warnings:
                    warning_id = warning.get('warning_id')
                    if warning_id and warning_id not in seen_warning_ids:
                        seen_warning_ids.add(warning_id)
                        all_warnings.append(warning)

            except Exception as e:
                logger.error(f"Error fetching warnings for location {location}: {str(e)}")
                continue

        return all_warnings

    def get_warnings_for_location(self, lat: float, lon: float, lang: str = 'en') -> List[Dict[str, Any]]:
        """
        Fetch warnings for specific coordinates from Geosphere API.
        
        Args:
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            lang (str): Language for the warnings (default: 'en')
            
        Returns:
            List[Dict]: List of processed warnings
        """
        try:
            logger.info(f"Fetching warnings for coordinates: lat={lat}, lon={lon}")
            
            url = f"{self.base_url}/getWarningsForCoords"
            params = {
                'lat': lat,
                'lon': lon,
                'lang': lang
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Raw API response for coordinates ({lat}, {lon}): {data}")
            
            if not isinstance(data, dict) or 'properties' not in data:
                logger.error("Invalid response format")
                return []

            warnings_data = data.get('properties', {}).get('warnings', [])
            processed_warnings = []

            for warning in warnings_data:
                if warning.get('type') != 'Warning':
                    continue
                    
                props = warning.get('properties', {})
                raw_info = props.get('rawinfo', {})
                
                try:
                    start_time = int(raw_info.get('start', 0))
                    end_time = int(raw_info.get('end', 0))
                    
                    processed_warning = {
                        'warning_id': f"w{props.get('warnid', '')}c{props.get('chgid', '')}v{props.get('verlaufid', '')}",
                        'type': self._convert_warning_type(raw_info.get('wtype')),
                        'severity': self._convert_severity(raw_info.get('wlevel')),
                        'start_time': datetime.fromtimestamp(start_time, tz=timezone.utc),
                        'end_time': datetime.fromtimestamp(end_time, tz=timezone.utc),
                        'description': props.get('text', ''),
                        'impact': props.get('auswirkungen', ''),
                        'recommendations': props.get('empfehlungen', ''),
                        'location': {
                            'lat': lat,
                            'lon': lon,
                            'area': data.get('properties', {}).get('location', {}).get('properties', {}).get('name', 'Unknown area')
                        },
                        'raw_data': raw_info
                    }
                    
                    logger.debug(f"Processed warning: {processed_warning}")
                    processed_warnings.append(processed_warning)
                    
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing warning {props.get('warnid')}: {str(e)}")
                    continue

            logger.info(f"Successfully fetched {len(processed_warnings)} warnings for location ({lat}, {lon})")
            return processed_warnings

        except requests.RequestException as e:
            logger.error(f"Error fetching warnings from Geosphere: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error processing Geosphere response: {str(e)}")
            return []

    def _convert_warning_type(self, wtype: Optional[int]) -> str:
        """Convert numeric warning type to string"""
        types = {
            1: "storm",
            2: "rain",
            3: "snow",
            4: "black_ice",
            5: "thunderstorm",
            6: "heat",
            7: "cold"
        }
        return types.get(wtype, "unknown")

    def _convert_severity(self, wlevel: Optional[int]) -> str:
        """Convert numeric warning level to severity string"""
        levels = {
            1: "low",      # yellow
            2: "medium",   # orange
            3: "high"      # red
        }
        return levels.get(wlevel, "low")
