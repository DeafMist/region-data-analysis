#!/usr/bin/env python3
"""Main pipeline for region analysis."""

import sys
import argparse
from typing import Dict, Optional
import pandas as pd
from config import LOG_LEVEL, set_region, get_region_config
from utils.logger import setup_logger
from parsers.cbr_parser import CBRParser
from parsers.osm_parser import OSMParser
from parsers.trudvsem_parser import TrudvsemParser
from analyzers.bank_analyzer import BankAnalyzer
from analyzers.matching_analyzer import MatchingAnalyzer
from analyzers.statistics_analyzer import StatisticsAnalyzer
from visualizers.chart_visualizer import ChartVisualizer
from visualizers.map_visualizer import MapVisualizer


class Pipeline:
    """Main pipeline orchestrating data collection, analysis, and visualization."""

    def __init__(self, region: str = None, vacancy_parser_class=None):
        """
        Initialize pipeline.

        Args:
            region: Region name
            vacancy_parser_class: Parser class to use (default: TrudvsemParser)
        """
        self.region = region
        self.vacancy_parser_class = vacancy_parser_class or TrudvsemParser
        self.logger = setup_logger("pipeline", LOG_LEVEL)
        self.data: Dict[str, Optional[pd.DataFrame]] = {}

    def run(self) -> bool:
        """Execute full analysis pipeline."""
        self.logger.info("=" * 60)
        self.logger.info(f"Starting Region Analysis Pipeline for region: {self.region}")
        self.logger.info("=" * 60)

        try:
            # Step 1: Download CBR reference
            self.logger.info("\n[1/6] Downloading CBR bank reference...")
            cbr_parser = CBRParser(region=self.region)
            cbr_df = cbr_parser.parse()
            self.data["cbr"] = cbr_df

            # Step 2: Parse OSM infrastructure
            self.logger.info("\n[2/6] Parsing OpenStreetMap infrastructure...")
            osm_parser = OSMParser(region=self.region)
            osm_data = osm_parser.parse(max_addresses=None)
            self.data.update(osm_data)

            # Step 3: Parse vacancies
            self.logger.info(
                f"\n[3/6] Parsing vacancies using {self.vacancy_parser_class.__name__}..."
            )
            vacancies_parser = self.vacancy_parser_class(region=self.region)
            vacancies_df = vacancies_parser.parse()
            self.data["vacancies"] = vacancies_df

            if vacancies_df.empty:
                self.logger.error("No vacancies data - stopping pipeline")
                return False

            # Step 4: Analyze banking sector
            self.logger.info("\n[4/6] Analyzing banking sector...")
            bank_analyzer = BankAnalyzer(region=self.region)
            bank_analyzer.analyze(
                self.data.get("banks", pd.DataFrame()), cbr_df=self.data.get("cbr")
            )
            self.logger.info("Bank analysis complete")

            # Step 5: Match vacancies to infrastructure
            self.logger.info("\n[5/6] Matching vacancies to infrastructure...")
            matching_analyzer = MatchingAnalyzer(
                max_distance_km=0.1, region=self.region
            )
            matched_df = matching_analyzer.analyze(self.data)
            self.data["matched"] = matched_df

            # Step 6: Generate statistics and visualizations
            self.logger.info("\n[6/6] Generating statistics and visualizations...")
            stats_analyzer = StatisticsAnalyzer(region=self.region)
            result = stats_analyzer.analyze(vacancies_df, matched_df=matched_df)

            if isinstance(result, tuple) and len(result) == 3:
                _, objects_agg_df, prof_composition_df = result
            else:
                objects_agg_df = pd.DataFrame()
                prof_composition_df = pd.DataFrame()

            self.logger.info(
                f"Generated aggregated data for {len(objects_agg_df)} objects"
            )
            self.logger.info(
                f"Generated professional composition for {len(prof_composition_df)} objects"
            )

            # Charts
            chart_viz = ChartVisualizer(region=self.region)
            chart_viz.visualize(
                vacancies_df, matched_df=matched_df, objects_agg_df=objects_agg_df
            )

            # Map
            banks_df = self.data.get("banks", pd.DataFrame())
            banks_only = (
                banks_df[banks_df["amenity"] == "bank"]
                if "amenity" in banks_df.columns
                else banks_df
            )
            atms_only = (
                banks_df[banks_df["amenity"] == "atm"]
                if "amenity" in banks_df.columns
                else pd.DataFrame()
            )

            map_data = {
                "Банки": banks_only,
                "Банкоматы": atms_only,
                "Производства": self.data.get("industries", pd.DataFrame()),
                "Салоны красоты": self.data.get("beauty", pd.DataFrame()),
                "Магазины": self.data.get("retail", pd.DataFrame()),
            }

            map_viz = MapVisualizer(region=self.region)
            map_file = map_viz.visualize(
                map_data,
                aggregated_df=objects_agg_df,
                prof_composition_df=prof_composition_df,
            )

            self.logger.info("=" * 60)
            self.logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            region_config = get_region_config(self.region)
            self.logger.info(f"Region: {region_config['name']}")
            self.logger.info("Statistics saved to data/processed/")
            self.logger.info("Charts saved to data/charts/")
            self.logger.info(f"Map saved to {map_file}")
            self.logger.info("=" * 60)

            return True

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False


def main():
    """Entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Analyze labor market and infrastructure"
    )
    parser.add_argument(
        "--region",
        "-r",
        type=str,
        default="belgorod",
        choices=["belgorod"],
        help="Region to analyze",
    )
    parser.add_argument(
        "--parser",
        "-p",
        type=str,
        default="trudvsem",
        choices=["trudvsem", "hh"],
        help="Vacancy parser to use (trudvsem or hh)",
    )

    args = parser.parse_args()

    # Set global region
    set_region(args.region)

    # Select parser
    if args.parser == "hh":
        from parsers.hh_parser import HhParser

        parser_class = HhParser
    else:
        from parsers.trudvsem_parser import TrudvsemParser

        parser_class = TrudvsemParser

    pipeline = Pipeline(region=args.region, vacancy_parser_class=parser_class)
    success = pipeline.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
