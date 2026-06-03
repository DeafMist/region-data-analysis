"""Analyzer for banking sector (banks and ATMs)."""

import pandas as pd
from core.analyzer import BaseAnalyzer


def is_bank_verified(name: str, cbr_df: pd.DataFrame) -> bool:
    """Check if bank name exists in CBR reference."""
    if not name or cbr_df is None or cbr_df.empty:
        return False

    name_lower = str(name).lower().strip()
    for bank_name in cbr_df["bank_name"]:
        if bank_name and (
            bank_name.lower() in name_lower or name_lower in bank_name.lower()
        ):
            return True
    return False


class BankAnalyzer(BaseAnalyzer):
    """Analyzer for bank and ATM distribution."""

    def __init__(self, region: str = None):
        super().__init__("bank")
        self.region = region

    def analyze(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Analyze banking sector.

        Args:
            data: DataFrame with banks (amenity, name, lat, lon, city)
            **kwargs: May contain 'cbr_df' for verification

        Returns:
            DataFrame with bank analysis summary
        """
        if data.empty:
            self.logger.warning("No bank data to analyze")
            return pd.DataFrame()

        df = data.copy()
        cbr_df = kwargs.get("cbr_df")

        # Split banks and ATMs
        if "amenity" in df.columns:
            banks = df[df["amenity"] == "bank"].copy()
            atms = df[df["amenity"] == "atm"].copy()
        else:
            banks = df.copy()
            atms = pd.DataFrame()

        banks = banks.dropna(subset=["name"])
        atms = atms.dropna(subset=["name"])

        # Basic stats
        result = {
            "total_banks": len(banks),
            "total_atms": len(atms),
            "unique_banks": banks["name"].nunique(),
            "unique_atm_brands": atms["name"].nunique(),
            "banks_distribution": banks["name"].value_counts().to_dict(),
            "atms_distribution": atms["name"].value_counts().to_dict(),
        }

        # City distribution
        if "city" in banks.columns:
            result["banks_by_city"] = banks["city"].value_counts().to_dict()
        if "city" in atms.columns and not atms.empty:
            result["atms_by_city"] = atms["city"].value_counts().to_dict()

        # CBR verification
        if cbr_df is not None and not cbr_df.empty:
            verified_mask = banks["name"].apply(lambda x: is_bank_verified(x, cbr_df))
            verified_banks = banks[verified_mask]

            result["verified_banks_count"] = verified_banks["name"].nunique()
            result["verified_banks_list"] = verified_banks["name"].unique().tolist()
            result["verified_banks_distribution"] = (
                verified_banks["name"].value_counts().to_dict()
            )

        # Convert to DataFrame for pipeline consistency
        summary_df = pd.DataFrame([result])

        # Save report
        region_prefix = self.region or "unknown"
        banks_dist = pd.DataFrame(
            result["banks_distribution"].items(),
            columns=["bank_name", "branches_count"],
        )
        banks_dist.to_csv(
            self._get_output_path(f"{region_prefix}_banks_distribution.csv"),
            index=False,
        )

        if result["atms_distribution"]:
            atms_dist = pd.DataFrame(
                result["atms_distribution"].items(),
                columns=["brand_name", "atms_count"],
            )
            atms_dist.to_csv(
                self._get_output_path(f"{region_prefix}_atms_distribution.csv"),
                index=False,
            )

        return summary_df

    def _get_output_path(self, filename: str) -> str:
        """Get output path for CSV files."""
        from config import PROCESSED_DATA_DIR

        return str(PROCESSED_DATA_DIR / filename)
