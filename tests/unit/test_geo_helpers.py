"""Unit tests for geo_helpers module."""

import pandas as pd
from unittest.mock import Mock, patch
from utils.geo_helpers import (
    to_float,
    calculate_distance_km,
    reverse_geocode,
    forward_geocode,
    get_rate_limited_geocoder,
)


class TestToFloat:
    """Tests for to_float function."""

    def test_float_input(self):
        assert to_float(123.45) == 123.45
        assert to_float(100) == 100.0

    def test_string_input(self):
        assert to_float("123.45") == 123.45
        assert to_float("123,45") == 123.45
        assert to_float("-50.5") == -50.5

    def test_invalid_string(self):
        assert to_float("abc") is None
        assert to_float("") is None

    def test_none_input(self):
        assert to_float(None) is None
        assert to_float(pd.NA) is None


class TestCalculateDistanceKm:
    """Tests for calculate_distance_km function."""

    def test_same_point(self):
        dist = calculate_distance_km(50.597, 36.587, 50.597, 36.587)
        assert dist < 0.01

    def test_belgrade_to_moscow(self):
        belgrade_lat, belgrade_lon = 44.7866, 20.4489
        moscow_lat, moscow_lon = 55.7558, 37.6173
        dist = calculate_distance_km(belgrade_lat, belgrade_lon, moscow_lat, moscow_lon)
        assert 1500 < dist < 1800

    def test_invalid_coordinates(self):
        dist = calculate_distance_km(None, 36.587, 50.597, 36.587)
        assert dist == float("inf")

        dist = calculate_distance_km(50.597, None, 50.597, 36.587)
        assert dist == float("inf")

    def test_belgorod_to_stary_oskol(self):
        belgorod_lat, belgorod_lon = 50.597, 36.587
        oskol_lat, oskol_lon = 51.298, 37.833
        dist = calculate_distance_km(belgorod_lat, belgorod_lon, oskol_lat, oskol_lon)
        assert 100 < dist < 130


class TestReverseGeocode:
    """Tests for reverse_geocode function."""

    @patch("utils.geo_helpers.Nominatim")
    def test_reverse_geocode_success(self, mock_nominatim):
        mock_geolocator = Mock()
        mock_location = Mock()
        mock_location.address = "г. Белгород, Россия"
        mock_geolocator.reverse.return_value = mock_location

        result = reverse_geocode(50.597, 36.587, mock_geolocator)
        assert result == "г. Белгород, Россия"
        mock_geolocator.reverse.assert_called_once_with("50.597, 36.587", language="ru")

    @patch("utils.geo_helpers.Nominatim")
    def test_reverse_geocode_no_location(self, mock_nominatim):
        mock_geolocator = Mock()
        mock_geolocator.reverse.return_value = None

        result = reverse_geocode(50.597, 36.587, mock_geolocator)
        assert result is None

    def test_reverse_geocode_invalid_coords(self):
        mock_geolocator = Mock()
        result = reverse_geocode(None, 36.587, mock_geolocator)
        assert result is None
        mock_geolocator.reverse.assert_not_called()


class TestForwardGeocode:
    """Tests for forward_geocode function."""

    @patch("utils.geo_helpers.Nominatim")
    def test_forward_geocode_success(self, mock_nominatim):
        mock_geolocator = Mock()
        mock_location = Mock()
        mock_location.latitude = 50.597
        mock_location.longitude = 36.587
        mock_geolocator.geocode.return_value = mock_location

        lat, lon = forward_geocode("г. Белгород", mock_geolocator)
        assert lat == 50.597
        assert lon == 36.587
        mock_geolocator.geocode.assert_called_once_with("г. Белгород", language="ru")

    @patch("utils.geo_helpers.Nominatim")
    def test_forward_geocode_no_location(self, mock_nominatim):
        mock_geolocator = Mock()
        mock_geolocator.geocode.return_value = None

        lat, lon = forward_geocode("Несуществующий адрес", mock_geolocator)
        assert lat is None
        assert lon is None


class TestGetRateLimitedGeocoder:
    """Tests for get_rate_limited_geocoder function."""

    def test_returns_tuple_of_three(self):
        geolocator, reverse_limiter, forward_limiter = get_rate_limited_geocoder()
        assert geolocator is not None
        assert reverse_limiter is not None
        assert forward_limiter is not None
