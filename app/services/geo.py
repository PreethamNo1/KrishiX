from typing import Optional, Tuple, List, Dict, Any
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from app.config import settings

_geolocator = Nominatim(user_agent="krishix_agri_matcher")


def geocode_location(location_name: str, state_region: str = "Karnataka, India") -> Optional[Tuple[float, float]]:
    """
    Geocodes a location query into (latitude, longitude).
    
    :param location_name: Name of village, town, or district.
    :param state_region: State/Country context to disambiguate.
    :return: (latitude, longitude) tuple or None if unresolved.
    """
    query = f"{location_name}, {state_region}" if state_region else location_name
    location = _geolocator.geocode(query, timeout=10)
    if location:
        return (location.latitude, location.longitude)
    return None


def find_buyers_in_radius(
    farmer_coords: Tuple[float, float],
    buyers: List[Dict[str, Any]],
    radius_km: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Filters and sorts buyers located within `radius_km` of the farmer coordinates.
    
    :param farmer_coords: (latitude, longitude) of the farmer.
    :param buyers: List of buyer dicts with 'lat', 'lon'.
    :param radius_km: Max distance threshold (defaults to settings.MATCH_RADIUS_KM).
    :return: List of matched buyer dicts including calculated 'distance' in km.
    """
    max_radius = radius_km if radius_km is not None else settings.MATCH_RADIUS_KM
    matched = []

    for buyer in buyers:
        try:
            buyer_coords = (float(buyer["lat"]), float(buyer["lon"]))
            dist = geodesic(farmer_coords, buyer_coords).km
            if dist <= max_radius:
                buyer_copy = dict(buyer)
                buyer_copy["distance"] = round(dist, 2)
                matched.append(buyer_copy)
        except (ValueError, TypeError, KeyError):
            continue

    # Sort matched buyers by nearest distance first
    matched.sort(key=lambda b: b["distance"])
    return matched

