"""Integration tests for HhParser."""

from unittest.mock import patch, MagicMock
from parsers.hh_parser import HhParser


class TestHhParser:
    """Integration tests for HhParser."""

    @patch("parsers.hh_parser.HhParser._authenticate")
    @patch("parsers.hh_parser.requests.get")
    def test_parse_vacancies(self, mock_get, mock_auth):
        with patch("parsers.hh_parser.HH_CLIENT_ID", "test"):
            with patch("parsers.hh_parser.HH_CLIENT_SECRET", "test"):
                mock_auth.return_value = True
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "items": [
                        {
                            "id": "1",
                            "name": "Программист",
                            "salary": {"from": 80000, "to": 100000},
                            "employer": {"name": "ООО Тест"},
                            "area": {"name": "Белгород"},
                            "address": {
                                "city": "Белгород",
                                "lat": "50.597",
                                "lng": "36.587",
                            },
                            "experience": {"id": "between1And3"},
                            "professional_roles": [{"name": "IT"}],
                            "published_at": "2024-01-01T00:00:00",
                        }
                    ],
                    "pages": 1,
                    "found": 1,
                }
                mock_get.return_value = mock_response

                parser = HhParser(region="belgorod")
                parser._access_token = "test_token"
                parser._token_expires_at = None
                result = parser.parse()

                assert not result.empty
                assert "job_name" in result.columns
                assert result.iloc[0]["job_name"] == "Программист"

    @patch("parsers.hh_parser.HhParser._authenticate")
    @patch("parsers.hh_parser.requests.get")
    def test_parse_no_credentials(self, mock_get, mock_auth):
        with patch("parsers.hh_parser.HH_CLIENT_ID", ""):
            with patch("parsers.hh_parser.HH_CLIENT_SECRET", ""):
                parser = HhParser(region="belgorod")
                result = parser.parse()
                assert result.empty
