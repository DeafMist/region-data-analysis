"""Integration tests for OSMParser."""

import pandas as pd
from unittest.mock import patch, MagicMock
from parsers.osm_parser import OSMParser


class TestOSMParser:
    """Integration tests for OSMParser."""

    def test_parse_banks_with_mock_data(self, tmp_path):
        """Test that parser correctly processes bank data."""
        mock_gdf = pd.DataFrame(
            {
                "geometry": [MagicMock(), MagicMock()],
                "name": ["Сбербанк", "ВТБ"],
                "brand": [None, None],
            }
        )
        mock_gdf.geometry.apply = lambda f: [(36.587, 50.597), (37.833, 51.298)]

        with patch("parsers.osm_parser.ox") as mock_ox:
            mock_ox.features_from_place.return_value = mock_gdf
            mock_ox.settings = MagicMock()

            parser = OSMParser(region="belgorod")
            with patch.object(parser, "_add_addresses", return_value=mock_gdf):
                result = parser._fetch_features({"amenity": ["bank"]}, "banks")

                assert result is not None
                assert len(result) == 2
                assert "name" in result.columns

    def test_parse_industries_with_mock_data(self, tmp_path):
        """Test that parser correctly processes industry data."""
        mock_gdf = pd.DataFrame(
            {"geometry": [MagicMock(), MagicMock()], "name": ["Завод", "Фабрика"]}
        )
        mock_gdf.geometry.apply = lambda f: [(36.587, 50.597), (37.833, 51.298)]

        with patch("parsers.osm_parser.ox") as mock_ox:
            mock_ox.features_from_place.return_value = mock_gdf
            mock_ox.settings = MagicMock()

            parser = OSMParser(region="belgorod")
            with patch.object(parser, "_add_addresses", return_value=mock_gdf):
                result = parser._fetch_features({"industrial": ["factory"]}, "industry")

                assert result is not None
                assert len(result) == 2
                assert "name" in result.columns

    def test_parse_empty(self):
        """Test that parser handles empty response."""
        with patch("parsers.osm_parser.ox") as mock_ox:
            mock_gdf = MagicMock()
            mock_gdf.empty = True
            mock_ox.features_from_place.return_value = mock_gdf
            mock_ox.settings = MagicMock()

            parser = OSMParser(region="belgorod")
            result = parser._fetch_features({"amenity": ["bank"]}, "banks")

            assert result is None

    def test_parse_impl_returns_dict(self):
        """Test that _parse_impl returns dictionary with expected keys."""
        with patch("parsers.osm_parser.OSMParser._fetch_features", return_value=None):
            parser = OSMParser(region="belgorod")
            result = parser._parse_impl()

            assert isinstance(result, dict)
