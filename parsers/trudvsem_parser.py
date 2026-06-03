"""Parser for vacancies from trudvsem.gov.ru API."""

import time
from typing import Dict, List
import pandas as pd
import requests
from config import (
    TRUDVSEM_API_BASE,
    VACANCIES_PAGE_SIZE,
    MAX_VACANCY_PAGES,
    get_region_config,
)
from core.parser import BaseVacancyParser
from utils.geo_helpers import to_float, get_rate_limited_geocoder
from utils.text_helpers import extract_city_from_address


class TrudvsemParser(BaseVacancyParser):
    """Parser for job vacancies from the official trudvsem API."""

    def __init__(self, region: str = None):
        super().__init__("trudvsem", region)

    def _parse_impl(self, **kwargs) -> pd.DataFrame:
        """
        Fetch all vacancies for region from trudvsem API.

        Returns:
            DataFrame with cleaned vacancies (each has lat/lon)
        """
        self.logger.info(
            f"Fetching vacancies from trudvsem API for region {self.region}"
        )

        region_config = get_region_config(self.region)
        region_code = region_config["code_trudvsem"]

        all_vacancies = []

        for page_num in range(MAX_VACANCY_PAGES):
            offset = page_num
            self.logger.debug(f"Fetching page {page_num} (offset {offset})")

            if page_num > 0:
                time.sleep(1)

            page_data = self._fetch_page(region_code, offset)

            if not page_data:
                self.logger.info(f"No more vacancies at page {page_num}")
                break

            all_vacancies.extend(page_data)
            self.logger.info(f"Total collected: {len(all_vacancies)}")

        if not all_vacancies:
            self.logger.warning("No vacancies found")
            return pd.DataFrame()

        df = pd.DataFrame(all_vacancies)

        # Remove duplicates
        df = df.drop_duplicates(subset=["id"])
        df = df.dropna(subset=["job_name"])

        # Clean numeric columns
        df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
        df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")
        df["experience"] = pd.to_numeric(df["experience"], errors="coerce")

        # Fill missing salary_min from salary_max
        mask = df["salary_min"].isna() & df["salary_max"].notna()
        df.loc[mask, "salary_min"] = df.loc[mask, "salary_max"]

        # Geocode and clean
        df = self._clean_and_geocode(df)

        return df

    def _fetch_page(self, region_code: str, offset: int) -> List[Dict]:
        """Fetch one page of vacancies."""
        url = f"{TRUDVSEM_API_BASE}/region/{region_code}"
        params = {"offset": offset, "limit": VACANCIES_PAGE_SIZE}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                self.logger.warning(f"HTTP {response.status_code} for offset {offset}")
                return []

            data = response.json()

            if data.get("status") != "200":
                self.logger.warning(
                    f"API error for offset {offset}: {data.get('status')}"
                )
                return []

            vacancies_list = data.get("results", {}).get("vacancies", [])
            parsed = []

            for item in vacancies_list:
                vacancy_data = item.get("vacancy", {})
                if vacancy_data:
                    parsed.append(self._parse_vacancy(vacancy_data))

            return parsed

        except Exception as e:
            self.logger.error(f"Error fetching offset {offset}: {e}")
            return []

    def _parse_vacancy(self, vacancy: Dict) -> Dict:
        """Parse single vacancy dict into flat record."""
        company = vacancy.get("company", {})
        addresses = vacancy.get("addresses", {}).get("address", [])
        addr = addresses[0] if addresses else {}

        requirement = vacancy.get("requirement", {})
        category = vacancy.get("category", {})

        # Convert coordinates to float safely
        lat_raw = addr.get("lat")
        lon_raw = addr.get("lng")

        lat = to_float(lat_raw)
        lon = to_float(lon_raw)

        address = addr.get("location")
        city = extract_city_from_address(address) if address else None

        return {
            "id": vacancy.get("id"),
            "job_name": vacancy.get("job-name"),
            "salary_min": vacancy.get("salary_min"),
            "salary_max": vacancy.get("salary_max"),
            "experience": requirement.get("experience"),
            "education": requirement.get("education"),
            "employer_name": company.get("name"),
            "address": address,
            "category": category.get("specialisation"),
            "lat": lat,
            "lon": lon,
            "city": city,
            "source_date": vacancy.get("creation-date"),
        }

    def _clean_and_geocode(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean vacancies and geocode missing coordinates/addresses.

        Args:
            df: Raw vacancies DataFrame

        Returns:
            Cleaned DataFrame with coordinates and addresses
        """
        self.logger.info("Cleaning and geocoding vacancies...")
        original_len = len(df)

        # Convert lat/lon to float
        if "lat" in df.columns:
            df["lat"] = df["lat"].apply(to_float)
        if "lon" in df.columns:
            df["lon"] = df["lon"].apply(to_float)

        # Remove rows without ANY location info
        has_coords = df["lat"].notna() & df["lon"].notna()
        has_address = df["address"].notna() & (df["address"] != "")
        df = df[has_coords | has_address].copy()
        self.logger.info(f"Removed {original_len - len(df)} rows without location data")

        geolocator, reverse_limiter, forward_limiter = get_rate_limited_geocoder()

        # Reverse geocode: has coords, no address
        missing_address = (
            (~df["address"].notna()) & df["lat"].notna() & df["lon"].notna()
        )
        if missing_address.any():
            self.logger.info(f"Reverse geocoding {missing_address.sum()} vacancies...")
            for idx in df[missing_address].index:
                addr = reverse_limiter(df.loc[idx, "lat"], df.loc[idx, "lon"])
                if addr:
                    df.loc[idx, "address"] = addr
                    df.loc[idx, "city"] = extract_city_from_address(addr)

        # Forward geocode: has address, no coords
        missing_coords = (~df["lat"].notna()) & df["address"].notna()
        if missing_coords.any():
            self.logger.info(f"Forward geocoding {missing_coords.sum()} vacancies...")
            for idx in df[missing_coords].index:
                lat, lon = forward_limiter(df.loc[idx, "address"])
                if lat is not None and lon is not None:
                    df.loc[idx, "lat"] = lat
                    df.loc[idx, "lon"] = lon

        # Final stats
        final_coords = df["lat"].notna() & df["lon"].notna()
        self.logger.info(f"Vacancies with coordinates: {final_coords.sum()}/{len(df)}")

        return df[final_coords].copy()
