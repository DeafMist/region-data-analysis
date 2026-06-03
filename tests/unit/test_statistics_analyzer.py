"""Unit tests for statistics_analyzer."""

import pandas as pd
from analyzers.statistics_analyzer import StatisticsAnalyzer


class TestStatisticsAnalyzer:
    """Tests for StatisticsAnalyzer class."""

    def setup_method(self):
        self.analyzer = StatisticsAnalyzer(region="test_region")

    def test_analyze_basic_stats(self, sample_vacancies_df):
        result_summary, result_objects, result_prof = self.analyzer.analyze(
            sample_vacancies_df
        )

        assert not result_summary.empty
        assert result_summary.iloc[0]["total_vacancies"] == 4
        assert result_summary.iloc[0]["unique_professions"] == 4
        assert result_summary.iloc[0]["avg_salary_total"] > 0

    def test_analyze_with_matched_data(self, sample_vacancies_df, sample_matched_df):
        result_summary, result_objects, result_prof = self.analyzer.analyze(
            sample_vacancies_df, matched_df=sample_matched_df
        )

        assert (
            result_summary.iloc[0]["objects_aggregated"] == "2 objects (saved to file)"
        )

    def test_analyze_category_distribution(self, sample_vacancies_df):
        result_summary, _, _ = self.analyzer.analyze(sample_vacancies_df)

        assert "category_counts" in result_summary.columns
        categories = result_summary.iloc[0]["category_counts"]
        assert isinstance(categories, dict)
        assert "Информационные технологии" in categories

    def test_analyze_salary_by_category(self, sample_vacancies_df):
        result_summary, _, _ = self.analyzer.analyze(sample_vacancies_df)

        assert "salary_by_category" in result_summary.columns
        salaries = result_summary.iloc[0]["salary_by_category"]
        assert isinstance(salaries, dict)
        assert salaries["Информационные технологии"] == 80000

    def test_analyze_top_jobs(self, sample_vacancies_df):
        result_summary, _, _ = self.analyzer.analyze(sample_vacancies_df)

        assert "top_jobs" in result_summary.columns
        top_jobs = result_summary.iloc[0]["top_jobs"]
        assert isinstance(top_jobs, dict)
        assert "Программист" in top_jobs

    def test_analyze_empty_dataframe(self):
        result_summary, result_objects, result_prof = self.analyzer.analyze(
            pd.DataFrame()
        )
        assert result_summary.empty
        assert result_objects.empty
        assert result_prof.empty

    def test_city_distribution(self, sample_vacancies_df):
        result_summary, _, _ = self.analyzer.analyze(sample_vacancies_df)

        assert "vacancies_by_city" in result_summary.columns
        cities = result_summary.iloc[0]["vacancies_by_city"]
        assert isinstance(cities, dict)
        assert cities["Белгород"] == 2
        assert cities["Старый Оскол"] == 1
        assert cities["Губкин"] == 1
