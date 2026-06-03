"""Parser for Central Bank of Russia bank reference."""

import xml.etree.ElementTree as ET

import pandas as pd
import requests

from config import CBR_BANK_LIST_URL
from core.parser import BaseParser


class CBRParser(BaseParser):
    """Parser for downloading bank names from CBR XML feed."""

    def __init__(self, region: str = None):
        super().__init__("cbr", region)

    def parse(self, **kwargs) -> pd.DataFrame:
        """
        Download and parse CBR bank list.

        Returns:
            DataFrame with column 'bank_name'
        """
        self.logger.info("Downloading CBR bank reference...")

        try:
            response = requests.get(CBR_BANK_LIST_URL, timeout=30)
            response.encoding = "windows-1251"

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code} from CBR")

            root = ET.fromstring(response.content)
            bank_names = []

            for record in root.findall(".//Record"):
                name_elem = record.find("ShortName")
                if name_elem is not None and name_elem.text:
                    bank_names.append(name_elem.text.strip())

            df = pd.DataFrame(bank_names, columns=["bank_name"])
            self.logger.info(f"Downloaded {len(df)} bank names from CBR")

            self._save_intermediate(df, "cbr_bank_reference.csv")

            return df

        except Exception as e:
            self.logger.error(f"Failed to download CBR reference: {e}")
            raise
