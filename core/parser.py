"""Abstract base class for all data parsers."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd
from config import DEFAULT_REGION, get_region_config
from core.schemas import VacancySchema, InfrastructureSchema
from utils.logger import setup_logger


class BaseParser(ABC):
    """Abstract parser that all concrete parsers must implement."""

    def __init__(self, name: str, region: str = None):
        self.name = name
        self.region = region or DEFAULT_REGION
        self.region_config = get_region_config(self.region)
        self.logger = setup_logger(f"parser.{name}")

    @abstractmethod
    def parse(self, **kwargs) -> Any:
        """
        Parse data from source.

        Args:
            **kwargs: Source-specific parameters (file paths, API URLs, etc.)

        Returns:
            Parsed data (DataFrame or Dict[str, DataFrame])

        Raises:
            Exception: If parsing fails
        """
        pass

    def _save_intermediate(self, df: pd.DataFrame, filename: str) -> None:
        """Save intermediate DataFrame to CSV."""
        from config import RAW_DATA_DIR

        # Add region prefix to filename
        region_prefix = self.region
        full_filename = f"{region_prefix}_{filename}"
        filepath = RAW_DATA_DIR / full_filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        self.logger.debug(f"Saved intermediate data to {filepath}")


class BaseVacancyParser(BaseParser):
    """Base parser for vacancy data with schema validation."""

    def parse(self, **kwargs) -> pd.DataFrame:
        """
        Parse vacancies and validate schema.

        Returns:
            DataFrame with VacancySchema columns
        """
        df = self._parse_impl(**kwargs)

        # Validate schema
        if not df.empty:
            VacancySchema.validate(df)
            self.logger.info(f"Parsed {len(df)} vacancies with valid schema")
        else:
            self.logger.warning("No vacancies parsed")

        return df

    @abstractmethod
    def _parse_impl(self, **kwargs) -> pd.DataFrame:
        """Implementation of parsing logic."""
        pass


class BaseInfrastructureParser(BaseParser):
    """Base parser for infrastructure data with schema validation."""

    def parse(self, **kwargs) -> Dict[str, pd.DataFrame]:
        """
        Parse infrastructure and validate schema.

        Returns:
            Dictionary with DataFrames conforming to InfrastructureSchema
        """
        result = self._parse_impl(**kwargs)

        # Validate each DataFrame
        for key, df in result.items():
            if not df.empty:
                InfrastructureSchema.validate(df)
                self.logger.info(f"Parsed {len(df)} {key} objects with valid schema")
            else:
                self.logger.warning(f"No {key} objects found")

        return result

    @abstractmethod
    def _parse_impl(self, **kwargs) -> Dict[str, pd.DataFrame]:
        """Implementation of parsing logic."""
        pass
