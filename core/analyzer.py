"""Abstract base class for all analyzers."""

from abc import ABC, abstractmethod
from typing import Any
import pandas as pd
from utils.logger import setup_logger


class BaseAnalyzer(ABC):
    """Abstract analyzer that all concrete analyzers must implement."""

    def __init__(self, name: str, region: str = None):
        self.name = name
        self.region = region
        self.logger = setup_logger(f"analyzer.{name}")

    @abstractmethod
    def analyze(self, data: Any, **kwargs) -> Any:
        """
        Perform analysis on input data.

        Args:
            data: Input data (DataFrame or Dict of DataFrames)
            **kwargs: Additional parameters (cbr_df, matched_df, etc.)

        Returns:
            Analysis results (DataFrame, Tuple of DataFrames, or other)
        """
        pass

    def _save_output(self, df: pd.DataFrame, filename: str) -> None:
        """Save analysis output to CSV."""
        from config import PROCESSED_DATA_DIR

        if self.region:
            filename = f"{self.region}_{filename}"
        filepath = PROCESSED_DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        self.logger.debug(f"Saved output to {filepath}")
