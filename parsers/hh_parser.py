"""Parser for vacancies from HeadHunter API with OAuth 2.0."""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import requests

from config import (
    HH_API_BASE,
    HH_OAUTH_URL,
    HH_CLIENT_ID,
    HH_CLIENT_SECRET,
    HH_VACANCIES_PER_PAGE,
    HH_MAX_PAGES,
    USER_AGENT_HH,
)
from core.parser import BaseVacancyParser
from utils.geo_helpers import to_float
from utils.text_helpers import extract_city_from_address


class HhParser(BaseVacancyParser):
    """
    Parser for job vacancies from HeadHunter API.

    Uses OAuth 2.0 authentication. Requires valid CLIENT_ID and CLIENT_SECRET.
    """

    def __init__(self, region: str = None):
        super().__init__("hh", region)
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_file = Path(__file__).parent.parent / "data" / ".hh_token.json"

        self._validate_credentials()
        self._load_token()
        if not self._ensure_valid_token():
            self._authenticate()

    def _validate_credentials(self) -> None:
        """Validate that HH credentials are configured."""
        if not HH_CLIENT_ID or not HH_CLIENT_SECRET:
            self.logger.warning(
                "HeadHunter credentials not configured. "
                "Please set HH_CLIENT_ID and HH_CLIENT_SECRET in .env file"
            )

    def _save_token(self) -> None:
        """Save token to file for persistence between runs."""
        if self._access_token and self._token_expires_at:
            token_data = {
                "access_token": self._access_token,
                "expires_at": self._token_expires_at.isoformat(),
            }
            try:
                self._token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self._token_file, "w") as f:
                    json.dump(token_data, f)
                self.logger.debug(f"Token saved to {self._token_file}")
            except Exception as e:
                self.logger.warning(f"Failed to save token: {e}")

    def _load_token(self) -> bool:
        """Load token from file if exists and not expired."""
        if not self._token_file.exists():
            return False

        try:
            with open(self._token_file, "r") as f:
                token_data = json.load(f)

            self._access_token = token_data.get("access_token")
            expires_at_str = token_data.get("expires_at")

            if expires_at_str:
                self._token_expires_at = datetime.fromisoformat(expires_at_str)

                if datetime.now() < self._token_expires_at:
                    self.logger.info("Loaded valid token from cache")
                    return True
                else:
                    self.logger.info("Cached token expired")
                    return False
        except Exception as e:
            self.logger.warning(f"Failed to load token: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication and user agent."""
        headers = {
            "User-Agent": USER_AGENT_HH,
            "HH-User-Agent": USER_AGENT_HH,
        }

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    def _authenticate(self) -> bool:
        """Obtain OAuth 2.0 access token from HeadHunter."""
        if not HH_CLIENT_ID or not HH_CLIENT_SECRET:
            self.logger.error("Cannot authenticate: missing credentials")
            return False

        try:
            headers = {
                "User-Agent": USER_AGENT_HH,
                "HH-User-Agent": USER_AGENT_HH,
                "Content-Type": "application/x-www-form-urlencoded",
            }

            response = requests.post(
                HH_OAUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": HH_CLIENT_ID,
                    "client_secret": HH_CLIENT_SECRET,
                },
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                self.logger.error(
                    f"OAuth failed: HTTP {response.status_code} - {response.text[:200]}"
                )
                return False

            data = response.json()
            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            self._save_token()

            self.logger.info("Successfully authenticated with HeadHunter API")
            return True

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def _ensure_valid_token(self) -> bool:
        """Ensure access token is valid, refresh if needed."""
        if not self._access_token:
            return False

        if self._token_expires_at and datetime.now() >= self._token_expires_at:
            self.logger.info("Token expired, re-authenticating...")
            return self._authenticate()

        return True

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None, method: str = "GET"
    ) -> Optional[Dict]:
        """Make authenticated request to HeadHunter API."""
        if not self._ensure_valid_token():
            return None

        url = f"{HH_API_BASE}{endpoint}"
        headers = self._get_headers()

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            else:
                response = requests.post(url, headers=headers, data=params, timeout=30)

            if response.status_code == 401:
                self.logger.warning("Token invalid, re-authenticating...")
                self._authenticate()
                return self._make_request(endpoint, params, method)

            if response.status_code != 200:
                self.logger.warning(
                    f"API error {response.status_code}: {response.text[:200]}"
                )
                return None

            return response.json()

        except requests.exceptions.Timeout:
            self.logger.warning(f"Request timeout for {endpoint}")
            return None
        except Exception as e:
            self.logger.error(f"Request failed for {endpoint}: {e}")
            return None

    def _get_area_id(self) -> int:
        """Get HH area ID for current region."""
        return self.region_config["code_hh"]

    def _parse_experience(self, experience: Optional[Dict]) -> Optional[float]:
        """Parse experience requirement to years."""
        if not experience:
            return None

        exp_id = experience.get("id", "")
        exp_map = {
            "noExperience": 0,
            "between1And3": 2,
            "between3And6": 4,
            "moreThan6": 7,
        }
        return exp_map.get(exp_id)

    def _parse_salary(
        self, salary: Optional[Dict]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Parse salary from HH vacancy."""
        if not salary:
            return None, None

        salary_from = salary.get("from")
        salary_to = salary.get("to")

        return salary_from, salary_to

    def _parse_vacancy(self, vacancy: Dict) -> Optional[Dict]:
        """Parse single HH vacancy to standard format."""
        try:
            salary = vacancy.get("salary")
            salary_min, salary_max = self._parse_salary(salary)

            experience = vacancy.get("experience")
            experience_years = self._parse_experience(experience)

            employer = vacancy.get("employer", {})
            employer_name = employer.get("name")

            area = vacancy.get("area", {})
            area_name = area.get("name")

            address_raw = vacancy.get("address") or {}

            address_parts = []
            city = address_raw.get("city") or area_name
            street = address_raw.get("street")
            building = address_raw.get("building")

            if city:
                address_parts.append(f"г. {city}")
            if street:
                address_parts.append(street)
            if building:
                address_parts.append(building)

            address = (
                ", ".join(address_parts) if address_parts else address_raw.get("raw")
            )

            lat = address_raw.get("lat")
            lon = address_raw.get("lng")
            lat = to_float(lat)
            lon = to_float(lon)

            professional_roles = vacancy.get("professional_roles", [])
            category = None
            if professional_roles:
                category = professional_roles[0].get("name")

            if not city and address:
                city = extract_city_from_address(address)

            published_at = vacancy.get("published_at")
            if published_at:
                published_at = published_at[:10]

            return {
                "id": str(vacancy.get("id")),
                "job_name": vacancy.get("name"),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "experience": experience_years,
                "education": None,
                "employer_name": employer_name,
                "address": address,
                "category": category,
                "lat": lat,
                "lon": lon,
                "city": city or area_name,
                "source_date": published_at,
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse HH vacancy: {e}")
            return None

    def _fetch_page(self, page: int) -> Tuple[List[Dict], int]:
        """Fetch one page of vacancies from HH API."""
        area_id = self._get_area_id()

        params = {
            "area": area_id,
            "page": page,
            "per_page": HH_VACANCIES_PER_PAGE,
        }

        self.logger.debug(
            f"Fetching page {page} with params: area={area_id}, per_page={HH_VACANCIES_PER_PAGE}"
        )

        response = self._make_request("/vacancies", params=params)

        if not response:
            return [], 0

        items = response.get("items", [])
        parsed = []

        for item in items:
            parsed_item = self._parse_vacancy(item)
            if parsed_item:
                parsed.append(parsed_item)

        total_pages = response.get("pages", 0)
        found = response.get("found", 0)

        self.logger.debug(
            f"Page {page}: found {len(items)} items, total {found} vacancies, pages {total_pages}"
        )

        return parsed, total_pages

    def _parse_impl(self, **kwargs) -> pd.DataFrame:
        """Fetch all vacancies for region from HeadHunter API."""
        self.logger.info(
            f"Fetching vacancies from HeadHunter API for region {self.region}"
        )

        if not HH_CLIENT_ID or not HH_CLIENT_SECRET:
            self.logger.error(
                "HeadHunter credentials not configured. "
                "Please set HH_CLIENT_ID and HH_CLIENT_SECRET in .env file"
            )
            return pd.DataFrame()

        all_vacancies = []

        for page in range(HH_MAX_PAGES):
            if page > 0:
                time.sleep(0.5)

            page_vacancies, total_pages = self._fetch_page(page)
            all_vacancies.extend(page_vacancies)
            self.logger.info(
                f"Page {page + 1}/{min(total_pages, HH_MAX_PAGES)}: collected {len(page_vacancies)} vacancies, total {len(all_vacancies)}"
            )

            if page + 1 >= total_pages or len(all_vacancies) >= 2000:
                break

        if not all_vacancies:
            self.logger.warning("No vacancies found from HeadHunter")
            return pd.DataFrame()

        df = pd.DataFrame(all_vacancies)

        df = df.drop_duplicates(subset=["id"])
        df = df.dropna(subset=["job_name"])

        df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
        df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")
        df["experience"] = pd.to_numeric(df["experience"], errors="coerce")

        # Fill salary_min from salary_max if missing
        mask_min = df["salary_min"].isna() & df["salary_max"].notna()
        df.loc[mask_min, "salary_min"] = df.loc[mask_min, "salary_max"]

        # Fill salary_max from salary_min if missing
        mask_max = df["salary_max"].isna() & df["salary_min"].notna()
        df.loc[mask_max, "salary_max"] = df.loc[mask_max, "salary_min"]

        # Fill city from address if missing
        mask_city = df["city"].isna() & df["address"].notna()
        if mask_city.any():
            df.loc[mask_city, "city"] = df.loc[mask_city, "address"].apply(
                extract_city_from_address
            )

        has_coords = df["lat"].notna() & df["lon"].notna()
        self.logger.info(f"Vacancies with coordinates: {has_coords.sum()}/{len(df)}")
        self.logger.info(f"Total vacancies from HeadHunter: {len(df)}")

        return df
