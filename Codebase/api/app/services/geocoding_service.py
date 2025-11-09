"""
Geocoding Service
Handles converting location text to coordinates using Nominatim (OpenStreetMap)
"""

import requests
import time
from typing import Optional, Tuple
from functools import lru_cache


class GeocodingService:
    """Service for geocoding locations to coordinates"""

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "CognizantEcoApp/1.0 (Sustainability Tracking)"

    # Common manufacturing locations (in-memory cache to avoid repeated API calls)
    COMMON_LOCATIONS = {
        "usa": (37.0902, -95.7129),
        "united states": (37.0902, -95.7129),
        "canada": (56.1304, -106.3468),
        "mexico": (23.6345, -102.5528),
        "italy": (41.8719, 12.5674),
        "france": (46.2276, 2.2137),
        "spain": (40.4637, -3.7492),
        "germany": (51.1657, 10.4515),
        "uk": (55.3781, -3.4360),
        "united kingdom": (55.3781, -3.4360),
        "china": (35.8617, 104.1954),
        "japan": (36.2048, 138.2529),
        "india": (20.5937, 78.9629),
        "brazil": (-14.2350, -51.9253),
        "australia": (-25.2744, 133.7751),
    }

    @classmethod
    @lru_cache(maxsize=500)
    def geocode(cls, location_text: str) -> Optional[Tuple[float, float]]:
        """
        Convert location text to coordinates (latitude, longitude).
        Uses in-memory cache and Nominatim API.

        Args:
            location_text: Location string (e.g., "USA", "Toronto, Ontario", "Italy")

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        if not location_text:
            return None

        # Normalize location text
        normalized = location_text.lower().strip()

        # Check common locations first (fast path)
        if normalized in cls.COMMON_LOCATIONS:
            return cls.COMMON_LOCATIONS[normalized]

        # Geocode with Nominatim
        return cls._geocode_nominatim(location_text)

    @classmethod
    def _geocode_nominatim(cls, location_text: str) -> Optional[Tuple[float, float]]:
        """
        Geocode using Nominatim API.
        Respects rate limiting (1 request per second).

        Args:
            location_text: Location string to geocode

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            # Nominatim requires 1 second between requests
            time.sleep(1)

            params = {
                "q": location_text,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }

            headers = {
                "User-Agent": cls.USER_AGENT
            }

            response = requests.get(
                cls.NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    lat = float(result['lat'])
                    lon = float(result['lon'])
                    print(f"Geocoded '{location_text}' → ({lat}, {lon})")
                    return (lat, lon)
                else:
                    print(f"No results found for '{location_text}'")
            else:
                print(f"Geocoding API error: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"Geocoding timeout for '{location_text}'")
        except Exception as e:
            print(f"Geocoding error for '{location_text}': {e}")

        return None

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.

        Args:
            lat1, lon1: Coordinates of first point (degrees)
            lat2, lon2: Coordinates of second point (degrees)

        Returns:
            Distance in kilometers
        """
        import math

        # Earth's radius in kilometers
        R = 6371

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return distance

    @classmethod
    def calculate_distance(cls, origin: str, destination: str) -> Optional[float]:
        """
        Calculate distance between two locations by name.

        Args:
            origin: Origin location text
            destination: Destination location text

        Returns:
            Distance in kilometers or None if geocoding fails
        """
        origin_coords = cls.geocode(origin)
        dest_coords = cls.geocode(destination)

        if not origin_coords or not dest_coords:
            return None

        return cls.haversine_distance(
            origin_coords[0], origin_coords[1],
            dest_coords[0], dest_coords[1]
        )
