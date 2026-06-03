"""Integration tests for CBRParser (with network mock)."""

import pytest
import pandas as pd
from unittest.mock import patch, Mock
from parsers.cbr_parser import CBRParser


class TestCBRParser:
    """Integration tests for CBRParser."""

    @patch("parsers.cbr_parser.requests.get")
    def test_parse_success(self, mock_get):
        # Mock XML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = """<?xml version="1.0" encoding="windows-1251"?>
        <ED807>
            <Record>
                <ShortName>СБЕРБАНК РОССИИ</ShortName>
            </Record>
            <Record>
                <ShortName>ВТБ</ShortName>
            </Record>
            <Record>
                <ShortName>АЛЬФА-БАНК</ShortName>
            </Record>
        </ED807>"""
        mock_get.return_value = mock_response

        parser = CBRParser(region="belgorod")
        result = parser.parse()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "bank_name" in result.columns
        assert result.iloc[0]["bank_name"] == "СБЕРБАНК РОССИИ"

    @patch("parsers.cbr_parser.requests.get")
    def test_parse_http_error(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        parser = CBRParser(region="belgorod")
        with pytest.raises(Exception, match="HTTP 500 from CBR"):
            parser.parse()
