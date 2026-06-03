"""Analyzer for matching vacancies with infrastructure objects."""

from typing import Dict
import pandas as pd
from core.analyzer import BaseAnalyzer
from utils.geo_helpers import calculate_distance_km, to_float
from utils.text_helpers import match_names, extract_city_from_address


class MatchingAnalyzer(BaseAnalyzer):
    """Match vacancies to infrastructure objects by name and distance."""

    def __init__(self, max_distance_km: float = 0.1, region: str = None):
        super().__init__("matching")
        self.max_distance_km = max_distance_km
        self.region = region

    def _match_vacancies_to_objects(
        self,
        vacancies: pd.DataFrame,
        objects_df: pd.DataFrame,
        object_type: str,
    ) -> pd.DataFrame:
        """
        Match vacancies to a specific type of infrastructure.

        Args:
            vacancies: Vacancies DataFrame with lat/lon/employer_name
            objects_df: Objects DataFrame with lat/lon/name
            object_type: Type identifier (bank, industry, etc.)

        Returns:
            DataFrame with matched vacancies
        """
        if vacancies.empty or objects_df.empty:
            return pd.DataFrame()

        matched_rows = []

        for _, vac in vacancies.iterrows():
            vac_lat = to_float(vac.get("lat"))
            vac_lon = to_float(vac.get("lon"))
            vac_name = vac.get("employer_name")

            if vac_lat is None or vac_lon is None:
                continue

            best_match = None
            best_distance = float("inf")

            for _, obj in objects_df.iterrows():
                obj_lat = to_float(obj.get("lat"))
                obj_lon = to_float(obj.get("lon"))
                obj_name = obj.get("name")

                if obj_lat is None or obj_lon is None:
                    continue

                if not match_names(vac_name, obj_name):
                    continue

                distance = calculate_distance_km(vac_lat, vac_lon, obj_lat, obj_lon)

                if distance <= self.max_distance_km and distance < best_distance:
                    best_distance = distance
                    best_match = obj

            if best_match is not None:
                vacancy_city = vac.get("city")
                if pd.isna(vacancy_city) and "address" in vac:
                    vacancy_city = extract_city_from_address(vac.get("address"))

                matched_rows.append(
                    {
                        "vacancy_id": vac.get("id"),
                        "vacancy_job": vac.get("job_name"),
                        "vacancy_employer": vac.get("employer_name"),
                        "vacancy_salary": vac.get("salary_min"),
                        "vacancy_city": vacancy_city,
                        "vacancy_category": vac.get("category", "Не указано"),
                        "object_name": best_match.get("name"),
                        "object_type": object_type,
                        "object_lat": to_float(best_match.get("lat")),
                        "object_lon": to_float(best_match.get("lon")),
                        "distance_km": round(best_distance, 3),
                    }
                )

        result = pd.DataFrame(matched_rows)
        self.logger.info(f"Matched {len(result)} vacancies to {object_type}")
        return result

    def analyze(self, data: Dict[str, pd.DataFrame], **kwargs) -> pd.DataFrame:
        """
        Match vacancies to all infrastructure types.

        Args:
            data: Dictionary with keys 'vacancies', 'banks', 'industries', 'beauty', 'retail'
            **kwargs: May override max_distance for specific types

        Returns:
            DataFrame with all matched vacancies
        """
        vacancies = data.get("vacancies")
        if vacancies is None or vacancies.empty:
            self.logger.warning("No vacancies for matching")
            return pd.DataFrame()

        matched_list = []

        # Define infrastructure types to match
        infrastructure_types = {
            "banks": "bank",
            "industries": "industry",
            "beauty": "beauty",
            "retail": "retail",
        }

        # Distance overrides for specific types
        distance_overrides = kwargs.get(
            "distance_overrides",
            {
                "industry": 0.5,
            },
        )

        for data_key, object_type in infrastructure_types.items():
            objects_df = data.get(data_key)
            if objects_df is not None and not objects_df.empty:
                objects_copy = objects_df.copy()

                # Ensure coordinates are float
                if "lat" in objects_copy.columns:
                    objects_copy["lat"] = objects_copy["lat"].apply(to_float)
                if "lon" in objects_copy.columns:
                    objects_copy["lon"] = objects_copy["lon"].apply(to_float)

                # Check if this object type has custom distance
                old_distance = self.max_distance_km
                if object_type in distance_overrides:
                    self.max_distance_km = distance_overrides[object_type]
                    self.logger.debug(
                        f"Using custom distance {self.max_distance_km}km for {object_type}"
                    )

                matched = self._match_vacancies_to_objects(
                    vacancies, objects_copy, object_type
                )
                if not matched.empty:
                    matched_list.append(matched)

                # Restore original distance
                self.max_distance_km = old_distance

        if not matched_list:
            self.logger.warning("No matches found")
            return pd.DataFrame()

        result = pd.concat(matched_list, ignore_index=True)
        self.logger.info(f"Total matched vacancies: {len(result)}")

        return result
