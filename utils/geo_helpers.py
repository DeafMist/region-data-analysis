"""Geospatial helper functions."""

import math
from typing import Optional, Tuple, Union
import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from sklearn.metrics.pairwise import haversine_distances
from config import GEOCODE_DELAY_SECONDS, USER_AGENT_NOMINATIM
from utils.logger import setup_logger

_logger = setup_logger("geo_helpers")


def to_float(value: Union[float, str, None]) -> Optional[float]:
    """
    Safely convert value to float.

    Args:
        value: Input value (could be float, string, or None)

    Returns:
        Float value or None if conversion fails
    """
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.replace(",", ".")
        try:
            return float(value)
        except ValueError:
            _logger.warning(f"Cannot convert '{value}' to float")
            return None

    return None


def calculate_distance_km(
    lat1: Union[float, str, None],
    lon1: Union[float, str, None],
    lat2: Union[float, str, None],
    lon2: Union[float, str, None],
) -> float:
    """
    Calculate Haversine distance between two points in kilometers.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in kilometers, or inf if any coordinate is invalid
    """
    lat1_f = to_float(lat1)
    lon1_f = to_float(lon1)
    lat2_f = to_float(lat2)
    lon2_f = to_float(lon2)

    if any(v is None for v in [lat1_f, lon1_f, lat2_f, lon2_f]):
        return float("inf")

    coords_1 = [math.radians(lat1_f), math.radians(lon1_f)]
    coords_2 = [math.radians(lat2_f), math.radians(lon2_f)]

    return haversine_distances([coords_1], [coords_2])[0][0] * 6371


def reverse_geocode(
    lat: Union[float, str, None], lon: Union[float, str, None], geolocator: Nominatim
) -> Optional[str]:
    """
    Get address from coordinates.

    Args:
        lat: Latitude
        lon: Longitude
        geolocator: Nominatim geocoder instance

    Returns:
        Address string or None
    """
    lat_f = to_float(lat)
    lon_f = to_float(lon)

    if lat_f is None or lon_f is None:
        return None

    try:
        location = geolocator.reverse(f"{lat_f}, {lon_f}", language="ru")
        return location.address if location else None
    except Exception as e:
        _logger.warning(f"Reverse geocoding failed for ({lat_f}, {lon_f}): {e}")
        return None


def forward_geocode(
    address: str, geolocator: Nominatim
) -> Tuple[Optional[float], Optional[float]]:
    """
    Get coordinates from address.

    Args:
        address: Address string
        geolocator: Nominatim geocoder instance

    Returns:
        Tuple of (latitude, longitude) or (None, None)
    """
    try:
        location = geolocator.geocode(address, language="ru")
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception as e:
        _logger.warning(f"Forward geocoding failed for '{address}': {e}")
        return None, None


def get_rate_limited_geocoder() -> Tuple[Nominatim, RateLimiter, RateLimiter]:
    """
    Create a rate-limited geocoder.

    Returns:
        Tuple of (geolocator, reverse_geocode_limiter, forward_geocode_limiter)
    """
    geolocator = Nominatim(user_agent=USER_AGENT_NOMINATIM)

    reverse_limiter = RateLimiter(
        lambda lat, lon: reverse_geocode(lat, lon, geolocator),
        min_delay_seconds=GEOCODE_DELAY_SECONDS,
    )

    forward_limiter = RateLimiter(
        lambda addr: forward_geocode(addr, geolocator),
        min_delay_seconds=GEOCODE_DELAY_SECONDS,
    )

    return geolocator, reverse_limiter, forward_limiter
