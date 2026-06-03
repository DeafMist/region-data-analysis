"""Integration tests for main Pipeline."""

from unittest.mock import patch, Mock
import pandas as pd
from main import Pipeline


class TestPipeline:
    """Integration tests for Pipeline class."""

    @patch("main.CBRParser")
    @patch("main.OSMParser")
    @patch("main.TrudvsemParser")
    @patch("main.BankAnalyzer")
    @patch("main.MatchingAnalyzer")
    @patch("main.StatisticsAnalyzer")
    @patch("main.ChartVisualizer")
    @patch("main.MapVisualizer")
    def test_pipeline_success(
        self,
        mock_map_viz,
        mock_chart_viz,
        mock_stats_analyzer,
        mock_matching_analyzer,
        mock_bank_analyzer,
        mock_vacancy_parser,
        mock_osm_parser,
        mock_cbr_parser,
    ):
        mock_cbr = Mock()
        mock_cbr.parse.return_value = pd.DataFrame({"bank_name": ["СБЕРБАНК"]})
        mock_cbr_parser.return_value = mock_cbr

        mock_osm = Mock()
        mock_osm.parse.return_value = {
            "banks": pd.DataFrame(
                {
                    "name": ["Сбербанк"],
                    "amenity": ["bank"],
                    "lat": [50.0],
                    "lon": [36.0],
                }
            )
        }
        mock_osm_parser.return_value = mock_osm

        mock_vacancy = Mock()
        mock_vacancy.parse.return_value = pd.DataFrame(
            {
                "id": ["1"],
                "job_name": ["Программист"],
                "salary_min": [80000],
                "lat": [50.0],
                "lon": [36.0],
                "category": ["IT"],
            }
        )
        mock_vacancy_parser.return_value = mock_vacancy
        mock_vacancy_parser.__name__ = "MockVacancyParser"

        mock_bank_analyzer.return_value.analyze.return_value = pd.DataFrame()
        mock_matching_analyzer.return_value.analyze.return_value = pd.DataFrame()
        mock_stats_analyzer.return_value.analyze.return_value = (
            pd.DataFrame(),
            pd.DataFrame({"object_name": ["Test"], "avg_salary": [50000]}),
            pd.DataFrame(),
        )

        mock_chart_viz.return_value.visualize.return_value = ["chart1.png"]
        mock_map_viz.return_value.visualize.return_value = "map.html"

        pipeline = Pipeline(region="belgorod", vacancy_parser_class=mock_vacancy_parser)
        success = pipeline.run()

        assert success is True
        mock_cbr_parser.assert_called_once()
        mock_osm_parser.assert_called_once()
        mock_vacancy_parser.assert_called_once()
        mock_bank_analyzer.return_value.analyze.assert_called_once()
        mock_matching_analyzer.return_value.analyze.assert_called_once()
        mock_stats_analyzer.return_value.analyze.assert_called_once()
