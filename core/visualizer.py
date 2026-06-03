"""Abstract base class for all visualizers."""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Union
from utils.logger import setup_logger


class BaseVisualizer(ABC):
    """Abstract visualizer that all concrete visualizers must implement."""

    def __init__(self, name: str, region: str = None):
        self.name = name
        self.region = region
        self.logger = setup_logger(f"visualizer.{name}")

    @abstractmethod
    def visualize(self, data: Any, **kwargs) -> Optional[Union[str, List[str]]]:
        """
        Generate visualization from data.

        Args:
            data: Input data (DataFrame, Dict of DataFrames, or other)
            **kwargs: Visualization parameters (matched_df, objects_agg_df, etc.)

        Returns:
            Path to saved visualization file, list of paths, or None
        """
        pass

    def _get_output_path(self, filename: str, subdir: str = None) -> str:
        """Get output path for visualization files."""
        from config import CHARTS_DIR, REPORTS_DIR

        target_dir = REPORTS_DIR if subdir == "reports" else CHARTS_DIR

        if self.region:
            filename = f"{self.region}_{filename}"

        return str(target_dir / filename)
