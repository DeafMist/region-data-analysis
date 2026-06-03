"""Parser for OpenStreetMap infrastructure data."""

import time
from typing import Dict, List, Optional
import osmnx as ox
import pandas as pd
from config import OVERPASS_ENDPOINTS
from core.parser import BaseInfrastructureParser
from utils.geo_helpers import get_rate_limited_geocoder

ox.settings.requests_timeout = 600
ox.settings.max_query_area_size = 27_000_000_000
ox.settings.use_cache = True
ox.settings.log_console = False
ox.settings.overpass_rate_limit = True


class OSMParser(BaseInfrastructureParser):
    """Parser for OSM infrastructure: banks, industries, beauty, retail."""

    def __init__(self, region: str = None):
        super().__init__("osm", region)
        self._current_endpoint_idx = 0
        ox.settings.overpass_endpoint = OVERPASS_ENDPOINTS[0]

    def _switch_endpoint(self) -> None:
        """Switch to next Overpass endpoint on failure."""
        self._current_endpoint_idx = (self._current_endpoint_idx + 1) % len(
            OVERPASS_ENDPOINTS
        )
        new_endpoint = OVERPASS_ENDPOINTS[self._current_endpoint_idx]
        ox.settings.overpass_endpoint = new_endpoint
        self.logger.warning(f"Switched to Overpass endpoint: {new_endpoint}")
        time.sleep(3)

    def _fetch_features(
        self,
        tags: Dict[str, List[str]],
        category: str,
        max_retries: int = len(OVERPASS_ENDPOINTS),
    ) -> Optional[pd.DataFrame]:
        """Fetch OSM features with retry and endpoint switching."""
        osm_place = self.region_config["osm_place"]

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Fetching {category} from {ox.settings.overpass_endpoint}"
                )
                time.sleep(2)

                gdf = ox.features_from_place(osm_place, tags)

                if gdf.empty:
                    self.logger.warning(f"No {category} found")
                    return None

                # Extract coordinates
                if "geometry" in gdf.columns:
                    coords = gdf.geometry.apply(self._get_coords)
                    gdf["lon"] = coords.apply(
                        lambda x: float(x[0]) if x[0] is not None else None
                    )
                    gdf["lat"] = coords.apply(
                        lambda x: float(x[1]) if x[1] is not None else None
                    )

                # Normalize name column
                if "name" not in gdf.columns:
                    gdf["name"] = pd.NA
                if "brand" in gdf.columns:
                    gdf["name"] = gdf["name"].fillna(gdf["brand"])

                # Add object_type for schema compliance
                gdf["object_type"] = category

                # Ensure coordinates are float
                gdf["lat"] = pd.to_numeric(gdf["lat"], errors="coerce")
                gdf["lon"] = pd.to_numeric(gdf["lon"], errors="coerce")

                self.logger.info(f"Found {len(gdf)} {category} objects")
                return gdf

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {category}: {e}")
                if attempt < max_retries - 1 and "No matching features" not in str(e):
                    self._switch_endpoint()
                else:
                    return None
        return None

    @staticmethod
    def _get_coords(geometry) -> tuple:
        """Extract (lon, lat) from geometry."""
        if geometry.geom_type == "Point":
            return geometry.x, geometry.y
        point = geometry.representative_point()
        return point.x, point.y

    def _add_addresses(
        self, gdf: pd.DataFrame, max_items: Optional[int] = None
    ) -> pd.DataFrame:
        """Add address column via reverse geocoding."""
        if gdf is None or gdf.empty:
            return gdf

        if max_items:
            gdf = gdf.head(max_items).copy()

        self.logger.info(f"Geocoding {len(gdf)} addresses...")

        _, reverse_limiter, _ = get_rate_limited_geocoder()

        gdf["address"] = gdf.apply(
            lambda row: reverse_limiter(row["lat"], row["lon"]),
            axis=1,
        )

        found = gdf["address"].notna().sum()
        self.logger.info(f"Obtained {found} addresses")
        return gdf

    def _parse_impl(self, **kwargs) -> Dict[str, pd.DataFrame]:
        """
        Parse all infrastructure types from OSM.

        Returns:
            Dictionary with keys: 'banks', 'industries', 'beauty', 'retail'
        """
        self.logger.info(f"Parsing OSM data for region: {self.region}")

        result = {}

        # Banks & ATMs
        banks = self._fetch_features({"amenity": ["bank", "atm"]}, "banks")
        if banks is not None:
            banks = self._add_addresses(banks, kwargs.get("max_addresses"))
            self._save_intermediate(banks, f"{self.region}_banks.csv")
            result["banks"] = banks

        # Industries (multiple tags for robustness)
        industrial_groups = [
            {"industrial": ["factory", "manufacturing"]},
            {"industrial": ["bakery", "brewery", "slaughterhouse", "grinding_mill"]},
            {"industrial": ["machine_shop", "metal_processing"]},
            {"industrial": ["brickyard", "concrete_plant", "sawmill"]},
        ]
        all_industries = []
        for tags in industrial_groups:
            gdf = self._fetch_features(tags, "industry")
            if gdf is not None:
                all_industries.append(gdf)
        if all_industries:
            industries = pd.concat(all_industries, ignore_index=True)
            industries = industries.drop_duplicates(subset=["geometry"])
            industries = self._add_addresses(industries, kwargs.get("max_addresses"))
            self._save_intermediate(industries, f"{self.region}_industries.csv")
            result["industries"] = industries

        # Beauty shops
        beauty = self._fetch_features(
            {
                "shop": ["beauty", "hairdresser", "massage"],
                "leisure": ["tanning_salon"],
            },
            "beauty",
        )
        if beauty is not None:
            beauty = self._add_addresses(beauty, kwargs.get("max_addresses"))
            self._save_intermediate(beauty, f"{self.region}_beauty.csv")
            result["beauty"] = beauty

        # Retail shops
        retail = self._fetch_features(
            {"shop": ["supermarket", "convenience", "general"]}, "retail"
        )
        if retail is not None:
            retail = self._add_addresses(retail, kwargs.get("max_addresses"))
            self._save_intermediate(retail, f"{self.region}_retail.csv")
            result["retail"] = retail

        return result
