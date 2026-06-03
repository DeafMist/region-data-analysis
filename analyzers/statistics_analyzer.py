"""Analyzer for statistical summaries of vacancies and matches."""

from typing import Tuple
import pandas as pd
from config import PROCESSED_DATA_DIR
from core.analyzer import BaseAnalyzer
from utils.text_helpers import extract_city_from_address


class StatisticsAnalyzer(BaseAnalyzer):
    """Generate regional labor market statistics."""

    def __init__(self, region: str = None):
        super().__init__("statistics", region)
        self.region = region

    def analyze(
        self, data: pd.DataFrame, **kwargs
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generate statistics from vacancies and matched data.

        Args:
            data: Vacancies DataFrame
            **kwargs: May contain 'matched_df' for object-level stats

        Returns:
            Tuple of (statistics_summary_df, objects_aggregated_df, prof_composition_df)
        """
        if data.empty:
            self.logger.warning("No data for statistics")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        vacancies = data.copy()
        matched_df = kwargs.get("matched_df", pd.DataFrame())

        if "city" not in vacancies.columns and "address" in vacancies.columns:
            vacancies["city"] = vacancies["address"].apply(extract_city_from_address)

        summary = {}

        # Category distribution
        if "category" in vacancies.columns:
            cat_counts = vacancies["category"].value_counts()
            summary["category_counts"] = cat_counts.to_dict()
            summary["category_percent"] = (
                (cat_counts / len(vacancies) * 100).round(1).to_dict()
            )

        # Salary by category
        if "category" in vacancies.columns and "salary_min" in vacancies.columns:
            salary_cat = (
                vacancies.groupby("category")["salary_min"]
                .mean()
                .round(0)
                .fillna(0)
                .astype(int)
            )
            summary["salary_by_category"] = salary_cat.to_dict()

        # Top jobs and employers
        if "job_name" in vacancies.columns:
            summary["top_jobs"] = (
                vacancies["job_name"].value_counts().head(10).to_dict()
            )
        if "employer_name" in vacancies.columns:
            summary["top_employers"] = (
                vacancies["employer_name"].value_counts().head(10).to_dict()
            )

        # Aggregates
        summary["total_vacancies"] = len(vacancies)
        summary["unique_professions"] = (
            vacancies["job_name"].nunique() if "job_name" in vacancies.columns else 0
        )
        summary["unique_employers"] = (
            vacancies["employer_name"].nunique()
            if "employer_name" in vacancies.columns
            else 0
        )
        summary["avg_salary_total"] = (
            vacancies["salary_min"].mean() if "salary_min" in vacancies.columns else 0
        )

        # Experience distribution
        if "experience" in vacancies.columns:
            exp_counts = vacancies["experience"].value_counts().sort_index()
            summary["experience_distribution"] = exp_counts.to_dict()

        # Education distribution
        if "education" in vacancies.columns:
            edu_counts = vacancies["education"].value_counts()
            summary["education_distribution"] = edu_counts.to_dict()

        # City distribution
        if "city" in vacancies.columns:
            city_counts = vacancies["city"].value_counts()
            city_counts = city_counts[city_counts.index.notna()]
            if not city_counts.empty:
                summary["vacancies_by_city"] = city_counts.to_dict()

                salary_by_city = (
                    vacancies.groupby("city")["salary_min"]
                    .mean()
                    .round(0)
                    .fillna(0)
                    .astype(int)
                )
                salary_by_city = salary_by_city[salary_by_city.index.notna()]
                if not salary_by_city.empty:
                    summary["salary_by_city"] = salary_by_city.to_dict()

        # Object-level aggregation and professional composition
        objects_agg_df = pd.DataFrame()
        prof_composition_df = pd.DataFrame()

        if not matched_df.empty:
            objects_agg_df, prof_composition_df = self._aggregate_by_objects(matched_df)

            if not objects_agg_df.empty:
                region_prefix = self.region or "unknown"
                objects_agg_df.to_csv(
                    PROCESSED_DATA_DIR / f"{region_prefix}_objects_aggregated.csv",
                    index=False,
                )
                summary["objects_aggregated"] = (
                    f"{len(objects_agg_df)} objects (saved to file)"
                )

            if not prof_composition_df.empty:
                prof_composition_df.to_csv(
                    PROCESSED_DATA_DIR
                    / f"{region_prefix}_profession_composition_by_object.csv",
                    index=False,
                )
                summary["profession_composition_saved"] = (
                    f"{len(prof_composition_df)} objects"
                )

        # Convert to DataFrame for pipeline
        summary_df = pd.DataFrame([summary])

        # Save to CSV
        region_prefix = self.region or "unknown"
        summary_df.to_csv(
            PROCESSED_DATA_DIR / f"{region_prefix}_statistics_summary.csv", index=False
        )

        return summary_df, objects_agg_df, prof_composition_df

    def _aggregate_by_objects(
        self, matched_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Aggregate matched vacancies by physical object (name + coordinates).

        Args:
            matched_df: DataFrame with matched vacancies

        Returns:
            Tuple of (objects_aggregated_df, prof_composition_df)
            prof_composition_df is in LONG format (each row: object_key, category, count)
        """
        if matched_df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Create unique object key
        matched_df["object_key"] = (
            matched_df["object_name"].astype(str)
            + "_"
            + matched_df["object_lat"].astype(str)
            + "_"
            + matched_df["object_lon"].astype(str)
        )

        # Average salary by object
        avg_salary = matched_df.groupby(
            ["object_name", "object_type", "object_key", "object_lat", "object_lon"]
        )["vacancy_salary"].mean()

        # Vacancy count by object
        vacancies_count = matched_df.groupby(
            ["object_name", "object_type", "object_key", "object_lat", "object_lon"]
        ).size()

        # Professional composition by object
        prof_composition = (
            matched_df.groupby(
                [
                    "object_key",
                    "object_name",
                    "object_type",
                    "object_lat",
                    "object_lon",
                    "vacancy_category",
                ]
            )
            .size()
            .reset_index(name="count")
        )

        # Filter out None/NaN categories
        prof_composition = prof_composition[
            prof_composition["vacancy_category"].notna()
        ]
        prof_composition = prof_composition[
            prof_composition["vacancy_category"] != "Не указано"
        ]

        # Sort for readability
        prof_composition = prof_composition.sort_values(
            ["object_name", "object_type", "count"], ascending=[True, True, False]
        ).reset_index(drop=True)

        # Prepare objects aggregated DataFrame
        objects_agg = pd.DataFrame(
            {
                "avg_salary": avg_salary.round(0).astype(int),
                "vacancies_count": vacancies_count,
            }
        ).reset_index()

        # Remove temporary key column
        objects_agg = objects_agg.drop(columns=["object_key"])

        # Return both DataFrames
        return objects_agg, prof_composition
