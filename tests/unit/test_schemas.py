"""Unit tests for data schemas."""

import pytest
import pandas as pd
from core.schemas import (
    VacancySchema,
    InfrastructureSchema,
    BankSchema,
    MatchedVacancySchema,
    StatisticsSchema,
)


class TestVacancySchema:
    """Tests for VacancySchema validation."""

    def test_valid_schema(self):
        df = pd.DataFrame(
            {
                "id": ["1", "2"],
                "job_name": ["Программист", "Учитель"],
                "salary_min": [80000.0, 50000.0],
                "salary_max": [120000.0, 60000.0],
                "experience": [2.0, 1.0],
                "education": ["Высшее", "Высшее"],
                "employer_name": ["ООО А", "ООО Б"],
                "address": ["ул. Ленина, 1", "ул. Пушкина, 2"],
                "category": ["IT", "Образование"],
                "lat": [50.597, 50.600],
                "lon": [36.587, 36.590],
                "source_date": ["2024-01-01", "2024-01-02"],
            }
        )
        result = VacancySchema.validate(df)
        assert result is True

    def test_missing_required_columns(self):
        df = pd.DataFrame(
            {
                "id": ["1"],
                "job_name": ["Программист"],
                "salary_min": [80000.0],
                # missing other columns
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            VacancySchema.validate(df)

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = VacancySchema.validate(df)
        assert result is True


class TestInfrastructureSchema:
    """Tests for InfrastructureSchema validation."""

    def test_valid_schema(self):
        df = pd.DataFrame(
            {
                "name": ["Сбербанк", "Магнит"],
                "lat": [50.597, 50.600],
                "lon": [36.587, 36.590],
                "address": ["ул. Ленина", "ул. Пушкина"],
                "object_type": ["bank", "retail"],
            }
        )
        result = InfrastructureSchema.validate(df)
        assert result is True

    def test_missing_required_columns(self):
        df = pd.DataFrame(
            {
                "name": ["Сбербанк"],
                "lat": [50.597],
                # missing lon, address, object_type
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            InfrastructureSchema.validate(df)


class TestBankSchema:
    """Tests for BankSchema validation."""

    def test_valid_bank_schema(self):
        df = pd.DataFrame(
            {
                "name": ["Сбербанк"],
                "lat": [50.597],
                "lon": [36.587],
                "address": ["ул. Ленина"],
                "object_type": ["bank"],
                "amenity": ["bank"],
            }
        )
        result = BankSchema.validate(df)
        assert result is True


class TestMatchedVacancySchema:
    """Tests for MatchedVacancySchema validation."""

    def test_valid_schema(self):
        df = pd.DataFrame(
            {
                "vacancy_id": ["1"],
                "vacancy_job": ["Программист"],
                "vacancy_employer": ["ООО А"],
                "vacancy_salary": [80000.0],
                "vacancy_city": ["Белгород"],
                "vacancy_category": ["IT"],
                "object_name": ["Сбербанк"],
                "object_type": ["bank"],
                "object_lat": [50.597],
                "object_lon": [36.587],
                "distance_km": [0.05],
            }
        )
        result = MatchedVacancySchema.validate(df)
        assert result is True


class TestStatisticsSchema:
    """Tests for StatisticsSchema validation."""

    def test_valid_schema(self):
        df = pd.DataFrame(
            {
                "total_vacancies": [1000],
                "unique_professions": [200],
                "unique_employers": [150],
                "avg_salary_total": [45000.0],
            }
        )
        result = StatisticsSchema.validate(df)
        assert result is True
