from pyproj import Transformer
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple, Any, Union
from ..config import Config

logger = logging.getLogger(__name__)

class GeosphereService:
    def __init__(self):
        self.api_url = "https://warnungen.zamg.at/wsapp/api/getWarnstatus"
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'InfoCal/1.0'
        }
        self.timeout = 10
        self.transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326")

    def get_warnings(self) -> List[Dict[str, Any]]:
        """
        Fetch warnings from Geosphere API.
        
        Returns:
            List[Dict]: List of processed warnings
        """
        try:
            logger.info("Fetching warnings from Geosphere API")
            response = requests.get(
                self.api_url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Raw Geosphere response: {data}")

            warnings = []
            if not isinstance(data, dict) or data.get('type') != 'FeatureCollection':
                logger.error("Invalid response format: not a FeatureCollection")
                return []

            features = data.get('features', [])
            logger.debug(f"Processing {len(features)} features")

            for feature in features:
                warning = self._process_warning_feature(feature)
                if warning:
                    warnings.append(warning)

            logger.info(f"Successfully fetched {len(warnings)} warnings")
            return warnings

        except requests.RequestException as e:
            logger.error(f"Error fetching warnings from Geosphere: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error processing Geosphere response: {str(e)}")
            return []

    def _process_warning_feature(self, feature: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single warning feature from the API response.
        
        Args:
            feature (Dict): Feature from GeoJSON response
            
        Returns:
            Optional[Dict]: Processed warning or None if invalid
        """
        try:
            logger.debug(f"Processing feature: {feature}")
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})

            # Basic validation
            if not properties or not geometry:
                logger.error("Missing properties or geometry in feature")
                return None

            coordinates = self._extract_coordinates(geometry)
            if not coordinates:
                logger.error("Could not extract valid coordinates")
                return None

            start_time = self._parse_timestamp(properties.get('start'))
            end_time = self._parse_timestamp(properties.get('end'))
            if not start_time or not end_time:
                logger.error("Invalid timestamps in warning")
                return None

            warning_type = self._convert_warning_type(properties.get('wtype'))
            severity = self._convert_severity(properties.get('wlevel'))
            areas = properties.get('gemeinden', [])

            warning = {
                'type': warning_type,
                'severity': severity,
                'start_time': start_time,
                'end_time': end_time,
                'location': {
                    'lat': coordinates[1],
                    'lon': coordinates[0],
                    'area': ', '.join(areas) if areas else 'Unknown area'
                },
                'warning_id': properties.get('warnid', str(datetime.now().timestamp())),
                'description': self._generate_description(warning_type, severity, areas),
                'raw_data': {
                    'wtype': properties.get('wtype'),
                    'wlevel': properties.get('wlevel'),
                    'areas': areas,
                    'geometry': geometry
                }
            }

            logger.debug(f"Processed warning: {warning}")
            return warning

        except Exception as e:
            logger.error(f"Error processing warning feature: {str(e)}", exc_info=True)
            return None

    def _extract_coordinates(self, geometry: Dict[str, Any]) -> Optional[List[float]]:
        """
        Extract and transform coordinates from GeoJSON geometry.
        
        Args:
            geometry (Dict): GeoJSON geometry object
        
        Returns:
            Optional[List[float]]: [longitude, latitude] or None if invalid
        """
        try:
            logger.debug(f"Extracting coordinates from geometry: {geometry}")
            if geometry.get('type') != 'MultiPolygon':
                logger.error(f"Unexpected geometry type: {geometry.get('type')}")
                return None

            coords = geometry.get('coordinates', [])[0][0][0]
            if len(coords) >= 2:
                result = self._transform_coordinates(coords[0], coords[1])
                if result:
                    lat, lon = result
                    logger.debug(f"Extracted and transformed coordinates: ({lat}, {lon})")
                    return [lon, lat]  # GeoJSON uses [lon, lat] order
            return None
        except (IndexError, TypeError) as e:
            logger.error(f"Error extracting coordinates: {str(e)}", exc_info=True)
            return None

    def _transform_coordinates(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        """
        Transform coordinates from Web Mercator (EPSG:3857) to WGS84 (EPSG:4326).
        
        Args:
            x (float): Web Mercator X coordinate
            y (float): Web Mercator Y coordinate
            
        Returns:
            Optional[Tuple[float, float]]: (latitude, longitude) in WGS84
        """
        try:
            lat, lon = self.transformer.transform(x, y)
            logger.debug(f"Transforming coordinates: ({x}, {y}) -> ({lat}, {lon})")
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
            logger.error(f"Transformed coordinates out of bounds: lat={lat}, lon={lon}")
            return None
        except Exception as e:
            logger.error(f"Error transforming coordinates: {str(e)}", exc_info=True)
            return None

    def _parse_timestamp(self, timestamp: Optional[Union[str, int]]) -> Optional[datetime]:
        """
        Convert Unix timestamp to datetime.
        
        Args:
            timestamp: Unix timestamp (string or integer)
            
        Returns:
            Optional[datetime]: Datetime object in UTC
        """
        try:
            if not timestamp:
                return None
            timestamp_int = int(timestamp)
            result = datetime.fromtimestamp(timestamp_int, tz=timezone.utc)
            logger.debug(f"Parsed timestamp {timestamp} to {result}")
            return result
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing timestamp {timestamp}: {str(e)}")
            return None

    def _convert_warning_type(self, wtype: Optional[int]) -> str:
        """
        Convert numeric warning type to string.
        
        Args:
            wtype: Warning type number from API
            
        Returns:
            str: Warning type string
        """
        types = {
            1: "storm",
            2: "rain",
            3: "snow",
            4: "black_ice",
            5: "thunderstorm",
            6: "heat",
            7: "cold"
        }
        result = types.get(wtype, "unknown")
        logger.debug(f"Converted warning type {wtype} to {result}")
        return result

    def _convert_severity(self, wlevel: Optional[int]) -> str:
        """
        Convert numeric warning level to severity string.
        
        Args:
            wlevel: Warning level number from API
            
        Returns:
            str: Severity string
        """
        levels = {
            1: "low",      # yellow
            2: "medium",   # orange
            3: "high"      # red
        }
        result = levels.get(wlevel, "low")
        logger.debug(f"Converted warning level {wlevel} to {result}")
        return result

    def _generate_description(self, warning_type: str, severity: str, areas: List[str]) -> str:
        """
        Generate a human-readable warning description.
        
        Args:
            warning_type (str): Type of warning
            severity (str): Warning severity
            areas (List[str]): Affected areas
            
        Returns:
            str: Formatted description
        """
        areas_text = ', '.join(areas) if areas else 'Unknown area'
        description = (
            f"{warning_type.title()} Warning\n"
            f"Severity Level: {severity.title()}\n"
            f"Affected Areas: {areas_text}"
        )
        logger.debug(f"Generated warning description: {description}")
        return description

    def is_valid_warning(self, warning: Dict[str, Any]) -> bool:
        """
        Check if a warning is valid and complete.
        
        Args:
            warning (Dict): Warning dictionary to validate
            
        Returns:
            bool: True if warning is valid
        """
        required_fields = ['type', 'severity', 'start_time', 'end_time', 'location', 'warning_id']
        return all(field in warning for field in required_fields)
