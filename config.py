"""Configuration constants for the Belgorod analysis project."""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
CHARTS_DIR = DATA_DIR / "charts"

# Create directories on import
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, CHARTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Region configuration
REGIONS: Dict[str, Dict[str, Any]] = {
    "belgorod": {
        "name": "Белгородская область",
        "name_ru": "Белгородская область",
        "code_trudvsem": "3100000000000",
        "code_hh": 1817,
        "center_lat": 50.597,
        "center_lon": 36.587,
        "zoom_start": 10,
        "cities": [
            "Белгород",
            "Старый Оскол",
            "Губкин",
            "Шебекино",
            "Алексеевка",
            "Валуйки",
            "Новый Оскол",
            "Строитель",
            "Бирюч",
            "Грайворон",
            "Короча",
            "Ракитное",
            "Чернянка",
        ],
        "osm_place": "Белгородская область, Россия",
    },
}

DEFAULT_REGION = "belgorod"
CURRENT_REGION = DEFAULT_REGION


def get_region_config(region_name: str = None) -> Dict[str, Any]:
    """Get configuration for a specific region."""
    name = region_name or CURRENT_REGION
    if name not in REGIONS:
        raise ValueError(f"Unknown region: {name}. Available: {list(REGIONS.keys())}")
    return REGIONS[name]


def set_region(region_name: str) -> None:
    """Change current region globally."""
    global CURRENT_REGION
    if region_name not in REGIONS:
        raise ValueError(
            f"Unknown region: {region_name}. Available: {list(REGIONS.keys())}"
        )
    CURRENT_REGION = region_name


# API and data sources
TRUDVSEM_API_BASE = "https://opendata.trudvsem.ru/api/v1/vacancies"
CBR_BANK_LIST_URL = "http://www.cbr.ru/scripts/XML_bic.asp"

HH_API_BASE = "https://api.hh.ru"
HH_OAUTH_URL = "https://hh.ru/oauth/token"

HH_CLIENT_ID = os.environ.get("HH_CLIENT_ID", "")
HH_CLIENT_SECRET = os.environ.get("HH_CLIENT_SECRET", "")

APP_NAME = "BelgorodSpatialAnalyzer"
APP_VERSION = "1.0"
CONTACT_EMAIL = os.environ.get("HH_CONTACT_EMAIL", "your-email@example.com")
USER_AGENT_HH = f"{APP_NAME}/{APP_VERSION} ({CONTACT_EMAIL})"

# Overpass API endpoints (fallback chain)
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api",
    "https://overpass.kumi.systems/api",
    "https://overpass.openstreetmap.ru/api",
    "https://overpass.private.coffee/api",
]

# Geocoding
GEOCODE_DELAY_SECONDS = 1
USER_AGENT_NOMINATIM = "belgorod_spatial_analyzer"

# Vacancies pagination
VACANCIES_PAGE_SIZE = 100
MAX_VACANCY_PAGES = 200

HH_VACANCIES_PER_PAGE = 100
HH_MAX_PAGES = 20  # max limit for hh

# Matching parameters
MATCHING_MAX_DISTANCE_KM = 0.1
MATCHING_MAX_DISTANCE_INDUSTRY_KM = 0.5

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
