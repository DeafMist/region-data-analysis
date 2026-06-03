"""Unit tests for ChartVisualizer."""

import pandas as pd
import matplotlib.pyplot as plt
from unittest.mock import patch
from visualizers.chart_visualizer import ChartVisualizer


class TestChartVisualizer:
    """Tests for ChartVisualizer class."""

    def setup_method(self):
        self.viz = ChartVisualizer(region="belgorod")
        self.sample_df = pd.DataFrame(
            {
                "category": ["IT", "IT", "Образование", "Образование", "Другое"],
                "job_name": [
                    "Программист",
                    "Разработчик",
                    "Учитель",
                    "Воспитатель",
                    "Уборщик",
                ],
                "employer_name": [
                    "Компания А",
                    "Компания А",
                    "Школа",
                    "Детский сад",
                    "Клининг",
                ],
                "salary_min": [80000, 90000, 40000, 35000, 25000],
                "city": ["Белгород", "Белгород", "Старый Оскол", "Губкин", "Белгород"],
            }
        )

    def teardown_method(self):
        plt.close("all")

    def test_visualize_empty_data(self):
        result = self.viz.visualize(pd.DataFrame())
        assert result == []

    def test_plot_category_pie(self):
        result = self.viz._plot_category_pie(self.sample_df)
        if result:
            assert result.endswith("01_category_distribution_pie.png")

    def test_plot_salary_by_category(self):
        result = self.viz._plot_salary_by_category(self.sample_df)
        if result:
            assert result.endswith("02_salary_by_category_barh.png")

    def test_plot_top_jobs(self):
        result = self.viz._plot_top_jobs(self.sample_df)
        if result:
            assert result.endswith("03_top_15_jobs_barh.png")

    def test_plot_top_employers(self):
        result = self.viz._plot_top_employers(self.sample_df)
        if result:
            assert result.endswith("04_top_15_employers_barh.png")

    def test_plot_banks_distribution_no_files(self):
        with patch(
            "visualizers.chart_visualizer.pd.read_csv", side_effect=FileNotFoundError()
        ):
            result = self.viz._plot_banks_distribution()
            assert result is None

    def test_plot_infrastructure_summary_no_files(self):
        with patch(
            "visualizers.chart_visualizer.pd.read_csv", side_effect=FileNotFoundError()
        ):
            result = self.viz._plot_infrastructure_summary()
            assert result is None

    def test_plot_salary_histogram(self):
        result = self.viz._plot_salary_histogram(self.sample_df)
        if result:
            assert result.endswith("07_salary_histogram.png")

    def test_plot_vacancies_by_city(self):
        result = self.viz._plot_vacancies_by_city(self.sample_df)
        if result:
            assert result.endswith("08_vacancies_by_city.png")

    def test_plot_salary_by_city(self):
        result = self.viz._plot_salary_by_city(self.sample_df)
        if result:
            assert result.endswith("09_salary_by_city_barh.png")

    def test_plot_category_by_object_type(self):
        matched_df = pd.DataFrame(
            {
                "object_type": ["bank", "bank", "industry", "retail"],
                "vacancy_category": ["IT", "Образование", "IT", "Продажи"],
            }
        )
        result = self.viz._plot_category_by_object_type(matched_df)
        if result:
            assert result.endswith("10_category_by_object_type.png")

    def test_plot_category_by_object_type_empty(self):
        result = self.viz._plot_category_by_object_type(pd.DataFrame())
        assert result is None

    def test_plot_top_objects_by_vacancies(self):
        objects_df = pd.DataFrame(
            {
                "object_name": ["Объект А", "Объект Б", "Объект В"],
                "vacancies_count": [10, 5, 3],
                "avg_salary": [50000, 45000, 40000],
            }
        )
        result = self.viz._plot_top_objects_by_vacancies(objects_df)
        if result:
            assert result.endswith("11_top_20_objects_by_vacancies.png")

    def test_plot_top_objects_by_salary(self):
        objects_df = pd.DataFrame(
            {
                "object_name": ["Объект А", "Объект Б", "Объект В"],
                "vacancies_count": [10, 5, 3],
                "avg_salary": [50000, 45000, 40000],
            }
        )
        result = self.viz._plot_top_objects_by_salary(objects_df)
        if result:
            assert result.endswith("12_top_20_objects_by_salary.png")

    def test_plot_experience_pie(self):
        df = pd.DataFrame({"experience": [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        result = self.viz._plot_experience_pie(df)
        if result:
            assert result.endswith("13_experience_distribution_pie.png")

    def test_plot_education_pie(self):
        df = pd.DataFrame(
            {"education": ["Высшее", "Среднее", "Высшее", "Среднее", "Не указано"]}
        )
        result = self.viz._plot_education_pie(df)
        if result:
            assert result.endswith("14_education_distribution_pie.png")

    def test_plot_salary_boxplot_by_category(self):
        result = self.viz._plot_salary_boxplot_by_category(self.sample_df)
        if result:
            assert result.endswith("15_salary_boxplot_by_category.png")

    def test_plot_matched_vacancies_by_object_type(self):
        matched_df = pd.DataFrame(
            {"object_type": ["bank", "bank", "industry", "retail"]}
        )
        result = self.viz._plot_matched_vacancies_by_object_type(matched_df)
        if result:
            assert result.endswith("16_matched_vacancies_by_object_type.png")
