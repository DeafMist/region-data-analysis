"""Data schemas and contracts for all modules."""

import pandas as pd


class VacancySchema:
    """
    Standard schema for vacancy data.

    All vacancy parsers must return DataFrame with these columns.
    """

    REQUIRED_COLUMNS = {
        "id": "object",
        "job_name": "object",
        "salary_min": "float64",
        "salary_max": "float64",
        "experience": "float64",
        "education": "object",
        "employer_name": "object",
        "address": "object",
        "category": "object",
        "lat": "float64",
        "lon": "float64",
        "source_date": "object",
    }

    OPTIONAL_COLUMNS = {
        "city": "object",
    }

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        """Validate that DataFrame matches required schema."""
        if df.empty:
            return True

        missing = set(cls.REQUIRED_COLUMNS.keys()) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Check dtypes
        for col, expected_dtype in cls.REQUIRED_COLUMNS.items():
            if col in df.columns:
                if df[col].dtype != expected_dtype and expected_dtype != "object":
                    # Allow coercion for numeric types
                    try:
                        df[col] = df[col].astype(expected_dtype)
                    except (TypeError, ValueError):
                        pass

        return True


class InfrastructureSchema:
    """
    Standard schema for infrastructure objects.

    All infrastructure parsers must return DataFrame with these columns.
    """

    REQUIRED_COLUMNS = {
        "name": "object",
        "lat": "float64",
        "lon": "float64",
        "address": "object",
        "object_type": "object",
    }

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        """Validate that DataFrame matches required schema."""
        if df.empty:
            return True

        missing = set(cls.REQUIRED_COLUMNS.keys()) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return True


class BankSchema(InfrastructureSchema):
    """Extended schema for bank-specific data."""

    REQUIRED_COLUMNS = InfrastructureSchema.REQUIRED_COLUMNS.copy()
    REQUIRED_COLUMNS.update(
        {
            "amenity": "object",
        }
    )

    OPTIONAL_COLUMNS = {
        "verified": "bool",
    }


class MatchedVacancySchema:
    """Schema for matched vacancies (vacancy + object)."""

    REQUIRED_COLUMNS = {
        "vacancy_id": "object",
        "vacancy_job": "object",
        "vacancy_employer": "object",
        "vacancy_salary": "float64",
        "vacancy_city": "object",
        "vacancy_category": "object",
        "object_name": "object",
        "object_type": "object",
        "object_lat": "float64",
        "object_lon": "float64",
        "distance_km": "float64",
    }

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        """Validate that DataFrame matches required schema."""
        if df.empty:
            return True

        missing = set(cls.REQUIRED_COLUMNS.keys()) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in matched data: {missing}")

        return True


class StatisticsSchema:
    """Schema for statistics output."""

    REQUIRED_COLUMNS = {
        "total_vacancies": "int64",
        "unique_professions": "int64",
        "unique_employers": "int64",
        "avg_salary_total": "float64",
    }

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        """Validate that DataFrame matches required schema."""
        if df.empty:
            return True

        missing = set(cls.REQUIRED_COLUMNS.keys()) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in statistics: {missing}")

        return True
