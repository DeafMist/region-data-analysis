"""Unit tests for matching_analyzer."""

import pandas as pd
from analyzers.matching_analyzer import MatchingAnalyzer


class TestMatchingAnalyzer:
    """Tests for MatchingAnalyzer class."""

    def setup_method(self):
        self.analyzer = MatchingAnalyzer(max_distance_km=0.1, region="test_region")

    def test_match_vacancies_to_objects(self, sample_vacancies_df, sample_banks_df):
        result = self.analyzer._match_vacancies_to_objects(
            sample_vacancies_df, sample_banks_df, "bank"
        )

        assert isinstance(result, pd.DataFrame)
        if not result.empty:
            assert "object_name" in result.columns
            assert "distance_km" in result.columns

    def test_no_match_due_to_distance(self, sample_vacancies_df):
        far_objects = pd.DataFrame(
            {
                "name": ["Сбербанк"],
                "lat": [60.0],
                "lon": [30.0],
                "address": ["г. Москва"],
            }
        )

        result = self.analyzer._match_vacancies_to_objects(
            sample_vacancies_df, far_objects, "bank"
        )
        assert result.empty

    def test_no_match_due_to_name(self, sample_vacancies_df, sample_retail_df):
        result = self.analyzer._match_vacancies_to_objects(
            sample_vacancies_df, sample_retail_df, "retail"
        )
        assert result.empty

    def test_analyze_all_types(
        self,
        sample_vacancies_df,
        sample_banks_df,
        sample_industries_df,
        sample_beauty_df,
        sample_retail_df,
    ):
        data = {
            "vacancies": sample_vacancies_df,
            "banks": sample_banks_df,
            "industries": sample_industries_df,
            "beauty": sample_beauty_df,
            "retail": sample_retail_df,
        }

        result = self.analyzer.analyze(data)

        assert isinstance(result, pd.DataFrame)
        if not result.empty:
            assert "object_type" in result.columns

    def test_analyze_no_vacancies(self, sample_banks_df):
        data = {"vacancies": pd.DataFrame(), "banks": sample_banks_df}
        result = self.analyzer.analyze(data)
        assert result.empty

    def test_analyze_custom_distance_overrides(
        self, sample_vacancies_df, sample_industries_df
    ):
        data = {
            "vacancies": sample_vacancies_df,
            "industries": sample_industries_df,
        }

        result = self.analyzer.analyze(data, distance_overrides={"industry": 0.5})
        assert isinstance(result, pd.DataFrame)
