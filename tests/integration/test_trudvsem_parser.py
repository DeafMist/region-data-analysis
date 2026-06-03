"""Integration tests for TrudvsemParser."""

from unittest.mock import patch, MagicMock
from parsers.trudvsem_parser import TrudvsemParser


class TestTrudvsemParser:
    """Integration tests for TrudvsemParser."""

    @patch("parsers.trudvsem_parser.requests.get")
    def test_parse_vacancies(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "200",
            "results": {
                "vacancies": [
                    {
                        "vacancy": {
                            "id": "1",
                            "job-name": "Программист",
                            "salary_min": 50000,
                            "salary_max": 70000,
                            "company": {"name": "ООО Тест"},
                            "addresses": {
                                "address": [
                                    {
                                        "location": "г. Белгород",
                                        "lat": "50.597",
                                        "lng": "36.587",
                                    }
                                ]
                            },
                            "requirement": {"experience": "1-3", "education": "Высшее"},
                            "category": {"specialisation": "IT"},
                            "creation-date": "2024-01-01",
                        }
                    }
                ]
            },
        }
        mock_get.return_value = mock_response

        parser = TrudvsemParser(region="belgorod")
        result = parser.parse()

        assert not result.empty
        assert "job_name" in result.columns
        assert result.iloc[0]["job_name"] == "Программист"

    @patch("parsers.trudvsem_parser.requests.get")
    def test_parse_no_vacancies(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "200",
            "results": {"vacancies": []},
        }
        mock_get.return_value = mock_response

        parser = TrudvsemParser(region="belgorod")
        result = parser.parse()

        assert result.empty

    @patch("parsers.trudvsem_parser.requests.get")
    def test_parse_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        parser = TrudvsemParser(region="belgorod")
        result = parser.parse()

        assert result.empty
