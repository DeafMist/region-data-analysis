"""Folium interactive map visualizer."""

from typing import Dict, Optional
import folium
import pandas as pd
from folium import plugins
from config import REPORTS_DIR, get_region_config
from core.visualizer import BaseVisualizer


class MapVisualizer(BaseVisualizer):
    """Generate interactive Folium map with infrastructure and vacancy data."""

    def __init__(self, region: str = None):
        super().__init__("map", region)
        self.region_config = get_region_config(region) if region else None

    def _get_color_by_type(self, object_type: str, amenity: str = None) -> str:
        """
        Return marker color by object type.

        Args:
            object_type: Type of object (bank, atm, industry, beauty, retail)
            amenity: Original OSM amenity tag for banks/ATMs

        Returns:
            Color name for folium marker
        """
        if amenity == "atm":
            return "lightblue"
        if amenity == "bank" or object_type == "bank":
            return "blue"

        colors = {
            "industry": "darkgreen",
            "beauty": "pink",
            "retail": "orange",
        }
        return colors.get(object_type, "gray")

    def _create_popup_html(self, row: pd.Series) -> str:
        """Create HTML for marker popup."""
        name = row.get("name", "Название не указано")
        if pd.isna(name):
            name = "Название не указано"

        obj_type = row.get("object_type", "")
        amenity = row.get("amenity", "")

        address = row.get("address", "Адрес не указан")
        if pd.isna(address):
            address = "Адрес не указан"

        vacancies = row.get("vacancies_count", 0)
        if pd.isna(vacancies):
            vacancies = 0

        salary = row.get("avg_salary", 0)
        if pd.isna(salary):
            salary = 0

        if amenity == "atm":
            type_ru = "Банкомат"
        elif amenity == "bank" or obj_type == "bank":
            type_ru = "Банк"
        else:
            type_map = {
                "industry": "Производство",
                "beauty": "Салон красоты",
                "retail": "Магазин",
            }
            type_ru = type_map.get(obj_type, obj_type)

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 350px;">
            <h4 style="margin: 0 0 5px 0; color: #2c3e50;">{name}</h4>
            <p style="margin: 3px 0; color: #7f8c8d; font-size: 12px;">{type_ru}</p>
            <hr style="margin: 5px 0;">
            <p style="margin: 5px 0;"><strong>Адрес:</strong> {address}</p>
        """

        if vacancies > 0:
            html += f"""
            <p style="margin: 5px 0;"><strong>Количество вакансий:</strong> {vacancies}</p>
            <p style="margin: 5px 0;"><strong>Средняя зарплата:</strong> {salary:,.0f} руб.</p>
            """
        else:
            html += (
                '<p style="margin: 5px 0; color: #95a5a6;">Нет данных о вакансиях</p>'
            )

        prof_composition = row.get("profession_composition", None)
        if (
            prof_composition
            and isinstance(prof_composition, dict)
            and len(prof_composition) > 0
        ):
            html += """
            <p style="margin: 5px 0;"><strong>Профессиональный состав:</strong></p>
            <ul style="margin: 0 0 5px 0; padding-left: 20px;">
            """
            for category, count in prof_composition.items():
                if category and not pd.isna(category) and category != "Не указано":
                    html += f"<li>{category}: {count} вакансий</li>"
            html += "</ul>"

        lat = row.get("lat")
        lon = row.get("lon")
        if lat and lon and not pd.isna(lat) and not pd.isna(lon):
            html += f"""
            <p style="margin: 5px 0; font-size: 10px; color: #95a5a6;">Координаты: {lat:.4f}, {lon:.4f}</p>
            """

        html += "</div>"
        return html

    def _prepare_layer_data(
        self,
        df: pd.DataFrame,
        object_type: str,
        aggregated_df: pd.DataFrame = None,
        prof_composition_df: pd.DataFrame = None,
    ) -> pd.DataFrame:
        """
        Prepare DataFrame for map layer with proper columns.

        Args:
            df: Raw infrastructure DataFrame
            object_type: Type identifier
            aggregated_df: DataFrame with aggregated vacancy data (avg_salary, vacancies_count)
            prof_composition_df: DataFrame with professional composition by object

        Returns:
            Prepared DataFrame with standardized columns
        """
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        # Ensure required columns exist
        if "object_type" not in df.columns:
            df["object_type"] = object_type

        if "amenity" not in df.columns and object_type in ["bank", "atm"]:
            df["amenity"] = object_type

        # Ensure coordinates are float
        if "lat" in df.columns:
            df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        if "lon" in df.columns:
            df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

        # Create object key for matching
        df["lat_rounded"] = df["lat"].round(4)
        df["lon_rounded"] = df["lon"].round(4)
        df["object_key"] = (
            df["name"].astype(str)
            + "_"
            + df["lat_rounded"].astype(str)
            + "_"
            + df["lon_rounded"].astype(str)
        )

        df["vacancies_count"] = 0
        df["avg_salary"] = 0
        df["profession_composition"] = None

        if aggregated_df is not None and not aggregated_df.empty:
            agg_df = aggregated_df.copy()
            if "object_lat" in agg_df.columns and "object_lon" in agg_df.columns:
                agg_df["lat_rounded"] = agg_df["object_lat"].round(4)
                agg_df["lon_rounded"] = agg_df["object_lon"].round(4)
                agg_df["object_key"] = (
                    agg_df["object_name"].astype(str)
                    + "_"
                    + agg_df["lat_rounded"].astype(str)
                    + "_"
                    + agg_df["lon_rounded"].astype(str)
                )

                salary_dict = dict(zip(agg_df["object_key"], agg_df["avg_salary"]))
                vacancies_dict = dict(
                    zip(agg_df["object_key"], agg_df["vacancies_count"])
                )

                df["avg_salary"] = (
                    df["object_key"].map(salary_dict).fillna(0).astype(int)
                )
                df["vacancies_count"] = (
                    df["object_key"].map(vacancies_dict).fillna(0).astype(int)
                )

        if prof_composition_df is not None and not prof_composition_df.empty:
            prof_df = prof_composition_df.copy()

            if "vacancy_category" in prof_df.columns and "count" in prof_df.columns:
                if "object_lat" in prof_df.columns and "object_lon" in prof_df.columns:
                    prof_df["lat_rounded"] = prof_df["object_lat"].round(4)
                    prof_df["lon_rounded"] = prof_df["object_lon"].round(4)
                    prof_df["object_key"] = (
                        prof_df["object_name"].astype(str)
                        + "_"
                        + prof_df["lat_rounded"].astype(str)
                        + "_"
                        + prof_df["lon_rounded"].astype(str)
                    )

                    comp_dict = {}
                    for obj_key in prof_df["object_key"].unique():
                        subset = prof_df[prof_df["object_key"] == obj_key]
                        comp_dict[obj_key] = dict(
                            zip(subset["vacancy_category"], subset["count"])
                        )

                    for idx, row in df.iterrows():
                        obj_key = row["object_key"]
                        if obj_key in comp_dict:
                            df.at[idx, "profession_composition"] = comp_dict[obj_key]

        # Clean up temporary columns
        df = df.drop(
            columns=["lat_rounded", "lon_rounded", "object_key"], errors="ignore"
        )
        df = df.dropna(subset=["lat", "lon"])

        return df

    def _add_heatmap_layer(
        self, map_obj: folium.Map, aggregated_df: pd.DataFrame
    ) -> None:
        """
        Add salary heatmap layer to map.

        Args:
            map_obj: Folium map object
            aggregated_df: DataFrame with aggregated vacancy data (avg_salary)
        """
        if aggregated_df is None or aggregated_df.empty:
            self.logger.info("No aggregated data available for heatmap")
            return

        points_with_salary = aggregated_df[
            (aggregated_df["avg_salary"] > 0)
            & (aggregated_df["object_lat"].notna())
            & (aggregated_df["object_lon"].notna())
        ].copy()

        if points_with_salary.empty:
            self.logger.info("No salary data available for heatmap")
            return

        heat_data = []
        salaries = []

        for _, row in points_with_salary.iterrows():
            salary = float(row["avg_salary"])
            lat = float(row["object_lat"])
            lon = float(row["object_lon"])
            heat_data.append([lat, lon, salary])
            salaries.append(salary)

        min_salary = min(salaries)
        max_salary = max(salaries)
        salary_range = max_salary - min_salary if max_salary > min_salary else 1

        gradient = {
            0.0: "blue",
            0.2: "cyan",
            0.4: "lime",
            0.6: "yellow",
            0.8: "red",
            1.0: "red",
        }

        plugins.HeatMap(
            heat_data,
            name="Тепловая карта зарплат",
            min_opacity=0.3,
            max_zoom=13,
            radius=15,
            blur=10,
            gradient=gradient,
        ).add_to(map_obj)

        self._add_legend(map_obj, min_salary, max_salary, salary_range)

    def _add_legend(
        self,
        map_obj: folium.Map,
        min_salary: float,
        max_salary: float,
        salary_range: float,
    ) -> None:
        """Add legend to map with salary ranges."""
        legend_html = f"""
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 12px; border-radius: 8px; border: 2px solid #ccc; font-family: Arial, sans-serif; font-size: 12px; max-width: 320px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
            <strong style="font-size: 14px;">Легенда</strong>
            <hr style="margin: 5px 0;">
            <strong>Зарплаты (руб.):</strong><br>
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 5px 0;">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 20px; height: 12px; background: blue;"></div>
                    <span>{int(min_salary)} - {int(min_salary + salary_range * 0.2)}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 20px; height: 12px; background: cyan;"></div>
                    <span>{int(min_salary + salary_range * 0.2)} - {int(min_salary + salary_range * 0.4)}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 20px; height: 12px; background: lime;"></div>
                    <span>{int(min_salary + salary_range * 0.4)} - {int(min_salary + salary_range * 0.6)}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 20px; height: 12px; background: yellow;"></div>
                    <span>{int(min_salary + salary_range * 0.6)} - {int(min_salary + salary_range * 0.8)}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 20px; height: 12px; background: red;"></div>
                    <span>{int(min_salary + salary_range * 0.8)} - {int(max_salary)}</span>
                </div>
            </div>
            <hr style="margin: 5px 0;">
            <strong>Объекты инфраструктуры:</strong><br>
            <div style="margin: 5px 0;">
                <div><span style="color: blue; font-size: 16px;">●</span> Банк</div>
                <div><span style="color: lightblue; font-size: 16px;">●</span> Банкомат</div>
                <div><span style="color: darkgreen; font-size: 16px;">●</span> Производство</div>
                <div><span style="color: pink; font-size: 16px;">●</span> Салон красоты</div>
                <div><span style="color: orange; font-size: 16px;">●</span> Магазин</div>
            </div>
        </div>
        """

        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_legend_without_heatmap(self, map_obj: folium.Map) -> None:
        """Add legend without salary heatmap when no salary data available."""
        legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 12px; border-radius: 8px; border: 2px solid #ccc; font-family: Arial, sans-serif; font-size: 12px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
            <strong style="font-size: 14px;">Легенда</strong>
            <hr style="margin: 5px 0;">
            <strong>Объекты инфраструктуры:</strong><br>
            <div style="margin: 5px 0;">
                <div><span style="color: blue; font-size: 16px;">●</span> Банк</div>
                <div><span style="color: lightblue; font-size: 16px;">●</span> Банкомат</div>
                <div><span style="color: darkgreen; font-size: 16px;">●</span> Производство</div>
                <div><span style="color: pink; font-size: 16px;">●</span> Салон красоты</div>
                <div><span style="color: orange; font-size: 16px;">●</span> Магазин</div>
            </div>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def visualize(
        self,
        data: Dict[str, pd.DataFrame],
        aggregated_df: pd.DataFrame = None,
        prof_composition_df: pd.DataFrame = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create interactive map with infrastructure markers and salary heatmap.

        Args:
            data: Dictionary with infrastructure DataFrames
            aggregated_df: DataFrame with aggregated vacancy data (avg_salary, vacancies_count)
            prof_composition_df: DataFrame with professional composition by object
            **kwargs: Additional parameters

        Returns:
            Path to saved HTML file
        """
        self.logger.info(f"Creating interactive map for region {self.region}")

        if self.region_config:
            center_lat = self.region_config["center_lat"]
            center_lon = self.region_config["center_lon"]
            zoom_start = self.region_config["zoom_start"]
        else:
            center_lat = 50.597
            center_lon = 36.587
            zoom_start = 10

        map_obj = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles="CartoDB positron",
            control_scale=True,
        )

        plugins.Fullscreen().add_to(map_obj)

        layer_mapping = {
            "Банки": "bank",
            "Банкоматы": "atm",
            "Производства": "industry",
            "Салоны красоты": "beauty",
            "Магазины": "retail",
        }

        for layer_name, object_type in layer_mapping.items():
            df = data.get(layer_name, pd.DataFrame())

            if df is None or df.empty:
                self.logger.debug(f"No data for layer {layer_name}")
                continue

            prepared_df = self._prepare_layer_data(
                df, object_type, aggregated_df, prof_composition_df
            )

            if prepared_df.empty:
                self.logger.warning(f"No valid coordinates for {layer_name}")
                continue

            marker_cluster = plugins.MarkerCluster(name=layer_name)

            for _, row in prepared_df.iterrows():
                lat = row.get("lat")
                lon = row.get("lon")

                if pd.isna(lat) or pd.isna(lon):
                    continue

                amenity = row.get("amenity", "")
                color = self._get_color_by_type(object_type, amenity)
                popup_html = self._create_popup_html(row)

                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=row.get("name", "Объект"),
                    icon=folium.Icon(color=color, icon="info-sign", prefix="glyphicon"),
                ).add_to(marker_cluster)

            marker_cluster.add_to(map_obj)

        if aggregated_df is not None and not aggregated_df.empty:
            self._add_heatmap_layer(map_obj, aggregated_df)
        else:
            self._add_legend_without_heatmap(map_obj)

        folium.LayerControl(collapsed=False).add_to(map_obj)

        region_prefix = self.region or "unknown"
        output_path = REPORTS_DIR / f"{region_prefix}_infrastructure_map.html"
        map_obj.save(str(output_path))

        self.logger.info(f"Map saved to {output_path}")

        return str(output_path)
