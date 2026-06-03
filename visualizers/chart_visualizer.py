"""Matplotlib-based chart generator."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from typing import List, Optional
from config import CHARTS_DIR, get_region_config
from core.visualizer import BaseVisualizer


def format_large_number(x: float, _) -> str:
    """Format large numbers as K/M."""
    if x >= 1_000_000:
        return f"{x / 1_000_000:.1f}M"
    elif x >= 1_000:
        return f"{x / 1_000:.0f}K"
    return str(int(x))


class ChartVisualizer(BaseVisualizer):
    """Generate charts using matplotlib and seaborn."""

    def __init__(self, region: str = None):
        super().__init__("charts", region)
        self.region_config = get_region_config(region) if region else None
        self.region_name = (
            self.region_config["name"] if self.region_config else "Регион"
        )

        plt.style.use("seaborn-v0_8-darkgrid")
        plt.rcParams["font.family"] = "DejaVu Sans"
        plt.rcParams["font.size"] = 12
        plt.rcParams["figure.figsize"] = (12, 8)
        plt.rcParams["figure.dpi"] = 100

    def visualize(
        self,
        data: pd.DataFrame,
        matched_df: pd.DataFrame = None,
        objects_agg_df: pd.DataFrame = None,
        **kwargs,
    ) -> List[str]:
        """
        Generate all charts from vacancy data.

        Args:
            data: Vacancies DataFrame
            matched_df: Matched vacancies DataFrame (for object-type charts)
            objects_agg_df: Aggregated objects DataFrame (for top objects charts)

        Returns:
            List of saved file paths
        """
        if data.empty:
            self.logger.warning("No data for charts")
            return []

        saved_files = []
        vacancies = data

        # Chart 1: Category distribution (pie)
        if "category" in vacancies.columns:
            filepath = self._plot_category_pie(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 2: Salary by category (horizontal bar)
        if "category" in vacancies.columns and "salary_min" in vacancies.columns:
            filepath = self._plot_salary_by_category(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 3: Top jobs (horizontal bar)
        if "job_name" in vacancies.columns:
            filepath = self._plot_top_jobs(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 4: Top employers (horizontal bar)
        if "employer_name" in vacancies.columns:
            filepath = self._plot_top_employers(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 5: Banks distribution (pie + bar)
        filepath = self._plot_banks_distribution()
        if filepath:
            saved_files.append(filepath)

        # Chart 6: Infrastructure summary (bar)
        filepath = self._plot_infrastructure_summary()
        if filepath:
            saved_files.append(filepath)

        # Chart 7: Salary histogram
        if "salary_min" in vacancies.columns:
            filepath = self._plot_salary_histogram(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 8: Vacancies by city (pie)
        if "city" in vacancies.columns:
            filepath = self._plot_vacancies_by_city(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 9: Salary by city (horizontal bar)
        if "city" in vacancies.columns and "salary_min" in vacancies.columns:
            filepath = self._plot_salary_by_city(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 10: Category by object type (stacked bar)
        if (
            matched_df is not None
            and not matched_df.empty
            and "vacancy_category" in matched_df.columns
        ):
            filepath = self._plot_category_by_object_type(matched_df)
            if filepath:
                saved_files.append(filepath)

        # Chart 11: Top objects by vacancies (horizontal bar)
        if (
            objects_agg_df is not None
            and not objects_agg_df.empty
            and "vacancies_count" in objects_agg_df.columns
        ):
            filepath = self._plot_top_objects_by_vacancies(objects_agg_df)
            if filepath:
                saved_files.append(filepath)

        # Chart 12: Top objects by salary (horizontal bar)
        if (
            objects_agg_df is not None
            and not objects_agg_df.empty
            and "avg_salary" in objects_agg_df.columns
        ):
            filepath = self._plot_top_objects_by_salary(objects_agg_df)
            if filepath:
                saved_files.append(filepath)

        # Chart 13: Experience distribution (pie)
        if "experience" in vacancies.columns:
            filepath = self._plot_experience_pie(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 14: Education distribution (pie)
        if "education" in vacancies.columns:
            filepath = self._plot_education_pie(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 15: Salary boxplot by category
        if "category" in vacancies.columns and "salary_min" in vacancies.columns:
            filepath = self._plot_salary_boxplot_by_category(vacancies)
            if filepath:
                saved_files.append(filepath)

        # Chart 16: Matched vacancies by object type (pie)
        if (
            matched_df is not None
            and not matched_df.empty
            and "object_type" in matched_df.columns
        ):
            filepath = self._plot_matched_vacancies_by_object_type(matched_df)
            if filepath:
                saved_files.append(filepath)

        self.logger.info(
            f"Generated {len(saved_files)} charts for region {self.region_name}"
        )
        return saved_files

    def _get_chart_path(self, filename: str) -> str:
        """Get region-aware chart path."""
        if self.region:
            filename = f"{self.region}_{filename}"
        return str(CHARTS_DIR / filename)

    def _plot_category_pie(self, vacancies: pd.DataFrame) -> Optional[str]:
        """Plot category distribution as pie chart."""
        cat_counts = vacancies["category"].value_counts()
        cat_counts = cat_counts[cat_counts.index.notna()]

        if cat_counts.empty:
            return None

        total = cat_counts.sum()
        main = cat_counts[cat_counts / total >= 0.02]
        others = cat_counts[cat_counts / total < 0.02]

        if len(others) > 0:
            result = pd.concat([main, pd.Series({"Другие": others.sum()})])
        else:
            result = main

        fig, ax = plt.subplots(figsize=(12, 10))
        colors = plt.cm.Set3(np.linspace(0, 1, len(result)))

        def autopct(pct):
            return f"{pct:.1f}%" if pct > 3 else ""

        ax.pie(
            result.values,
            labels=result.index,
            autopct=autopct,
            colors=colors,
            startangle=90,
            textprops={"fontsize": 11},
        )

        ax.set_title(
            f"Распределение вакансий по категориям профессий\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        path = self._get_chart_path("01_category_distribution_pie.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_salary_by_category(self, vacancies: pd.DataFrame) -> Optional[str]:
        """Plot salary by category as horizontal bar chart."""
        filtered = vacancies[
            (vacancies["salary_min"] > 0) & vacancies["category"].notna()
        ]
        if filtered.empty:
            return None

        salary_cat = (
            filtered.groupby("category")["salary_min"]
            .mean()
            .sort_values(ascending=False)
            .head(20)
        )

        if salary_cat.empty:
            return None

        fig, ax = plt.subplots(figsize=(14, 10))
        colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(salary_cat)))
        bars = ax.barh(
            range(len(salary_cat)),
            salary_cat.values,
            color=colors,
            edgecolor="black",
            linewidth=0.5,
        )

        ax.set_yticks(range(len(salary_cat)))
        ax.set_yticklabels(salary_cat.index, fontsize=10)
        ax.set_xlabel("Средняя зарплата (руб.)", fontsize=12)
        ax.set_title(
            f"Средняя зарплата по категориям профессий\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.xaxis.set_major_formatter(FuncFormatter(format_large_number))
        ax.invert_yaxis()

        for bar, val in zip(bars, salary_cat.values):
            ax.text(
                bar.get_width() + 500,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}".replace(",", " "),
                ha="left",
                va="center",
                fontsize=9,
            )

        ax.grid(axis="x", alpha=0.3)

        path = self._get_chart_path("02_salary_by_category_barh.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_top_jobs(self, vacancies: pd.DataFrame, top_n: int = 15) -> Optional[str]:
        """Plot top N job titles."""
        top_jobs = vacancies["job_name"].value_counts().head(top_n)

        if top_jobs.empty:
            return None

        fig, ax = plt.subplots(figsize=(12, 10))
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(top_jobs)))
        bars = ax.barh(
            range(len(top_jobs)),
            top_jobs.values,
            color=colors,
            edgecolor="black",
            linewidth=0.5,
        )

        ax.set_yticks(range(len(top_jobs)))
        ax.set_yticklabels(top_jobs.index, fontsize=9)
        ax.set_xlabel("Количество вакансий", fontsize=12)
        ax.set_title(
            f"Топ-{top_n} самых востребованных профессий\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.invert_yaxis()

        for bar, val in zip(bars, top_jobs.values):
            ax.text(
                bar.get_width() + 2,
                bar.get_y() + bar.get_height() / 2,
                str(val),
                va="center",
                fontsize=9,
                fontweight="bold",
            )

        ax.grid(axis="x", alpha=0.3)

        path = self._get_chart_path(f"03_top_{top_n}_jobs_barh.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_top_employers(
        self, vacancies: pd.DataFrame, top_n: int = 15
    ) -> Optional[str]:
        """Plot top N employers."""
        top_employers = vacancies["employer_name"].value_counts().head(top_n)

        if top_employers.empty:
            return None

        fig, ax = plt.subplots(figsize=(14, 10))
        colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(top_employers)))
        bars = ax.barh(
            range(len(top_employers)),
            top_employers.values,
            color=colors,
            edgecolor="black",
            linewidth=0.5,
        )

        ax.set_yticks(range(len(top_employers)))
        ax.set_yticklabels(top_employers.index, fontsize=10)
        ax.set_xlabel("Количество вакансий", fontsize=12)
        ax.set_title(
            f"Топ-{top_n} работодателей по количеству вакансий\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.invert_yaxis()

        for bar, val in zip(bars, top_employers.values):
            ax.text(
                bar.get_width() + 2,
                bar.get_y() + bar.get_height() / 2,
                str(val),
                va="center",
                fontsize=9,
                fontweight="bold",
            )

        ax.grid(axis="x", alpha=0.3)

        path = self._get_chart_path(f"04_top_{top_n}_employers_barh.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_banks_distribution(self) -> Optional[str]:
        """Plot banks and ATMs distribution."""
        try:
            banks_dist_path = f"data/processed/{self.region}_banks_distribution.csv"
            atms_dist_path = f"data/processed/{self.region}_atms_distribution.csv"

            banks_df = (
                pd.read_csv(banks_dist_path, encoding="utf-8-sig")
                if pd.io.common.file_exists(banks_dist_path)
                else pd.DataFrame()
            )
            atms_df = (
                pd.read_csv(atms_dist_path, encoding="utf-8-sig")
                if pd.io.common.file_exists(atms_dist_path)
                else pd.DataFrame()
            )

            if banks_df.empty and atms_df.empty:
                return None

            fig, axes = plt.subplots(1, 2, figsize=(14, 7))

            if not banks_df.empty:
                top_banks = banks_df.head(10)
                colors = plt.cm.tab20(np.linspace(0, 1, len(top_banks)))
                bars = axes[0].barh(
                    range(len(top_banks)),
                    top_banks["branches_count"].values,
                    color=colors,
                    edgecolor="black",
                    linewidth=0.5,
                )
                axes[0].set_yticks(range(len(top_banks)))
                axes[0].set_yticklabels(top_banks["bank_name"].values, fontsize=9)
                axes[0].set_xlabel("Количество отделений", fontsize=11)
                axes[0].set_title(
                    "Топ-10 банков по количеству отделений",
                    fontsize=13,
                    fontweight="bold",
                )
                axes[0].invert_yaxis()
                axes[0].grid(axis="x", alpha=0.3)

                for bar, val in zip(bars, top_banks["branches_count"].values):
                    axes[0].text(
                        bar.get_width() + 1,
                        bar.get_y() + bar.get_height() / 2,
                        str(val),
                        va="center",
                        fontsize=9,
                    )

            if not atms_df.empty:
                top_atms = atms_df.head(10)
                colors = plt.cm.tab20(np.linspace(0, 1, len(top_atms)))
                bars = axes[1].barh(
                    range(len(top_atms)),
                    top_atms["atms_count"].values,
                    color=colors,
                    edgecolor="black",
                    linewidth=0.5,
                )
                axes[1].set_yticks(range(len(top_atms)))
                axes[1].set_yticklabels(top_atms["brand_name"].values, fontsize=9)
                axes[1].set_xlabel("Количество банкоматов", fontsize=11)
                axes[1].set_title(
                    "Топ-10 банков по количеству банкоматов",
                    fontsize=13,
                    fontweight="bold",
                )
                axes[1].invert_yaxis()
                axes[1].grid(axis="x", alpha=0.3)

                for bar, val in zip(bars, top_atms["atms_count"].values):
                    axes[1].text(
                        bar.get_width() + 1,
                        bar.get_y() + bar.get_height() / 2,
                        str(val),
                        va="center",
                        fontsize=9,
                    )

            if banks_df.empty and not atms_df.empty:
                axes[0].set_visible(False)

            plt.tight_layout()
            path = self._get_chart_path("05_banks_distribution.png")
            fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            return path

        except Exception as e:
            self.logger.warning(f"Could not plot banks distribution: {e}")
            return None

    def _plot_infrastructure_summary(self) -> Optional[str]:
        """Plot infrastructure objects summary."""
        try:
            banks_path = f"data/raw/{self.region}_banks.csv"
            industries_path = f"data/raw/{self.region}_industries.csv"
            beauty_path = f"data/raw/{self.region}_beauty.csv"
            retail_path = f"data/raw/{self.region}_retail.csv"

            banks_df = (
                pd.read_csv(banks_path, encoding="utf-8-sig")
                if pd.io.common.file_exists(banks_path)
                else pd.DataFrame()
            )
            industries_df = (
                pd.read_csv(industries_path, encoding="utf-8-sig")
                if pd.io.common.file_exists(industries_path)
                else pd.DataFrame()
            )
            beauty_df = (
                pd.read_csv(beauty_path, encoding="utf-8-sig")
                if pd.io.common.file_exists(beauty_path)
                else pd.DataFrame()
            )
            retail_df = (
                pd.read_csv(retail_path, encoding="utf-8-sig")
                if pd.io.common.file_exists(retail_path)
                else pd.DataFrame()
            )

            categories = []
            counts = []

            if not banks_df.empty:
                if "amenity" in banks_df.columns:
                    categories.append("Банки")
                    counts.append(len(banks_df[banks_df["amenity"] == "bank"]))
                    categories.append("Банкоматы")
                    counts.append(len(banks_df[banks_df["amenity"] == "atm"]))
                else:
                    categories.append("Банки")
                    counts.append(len(banks_df))

            if not industries_df.empty:
                categories.append("Производства")
                counts.append(len(industries_df))

            if not beauty_df.empty:
                categories.append("Салоны красоты")
                counts.append(len(beauty_df))

            if not retail_df.empty:
                categories.append("Магазины")
                counts.append(len(retail_df))

            if not categories:
                return None

            fig, ax = plt.subplots(figsize=(12, 8))
            colors = plt.cm.Paired(np.linspace(0, 1, len(categories)))
            bars = ax.bar(
                categories, counts, color=colors, edgecolor="black", linewidth=1
            )

            for bar, count in zip(bars, counts):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(counts) * 0.02,
                    str(count),
                    ha="center",
                    va="bottom",
                    fontsize=12,
                    fontweight="bold",
                )

            ax.set_ylabel("Количество объектов", fontsize=12)
            ax.set_title(
                f"Объекты инфраструктуры\n{self.region_name}",
                fontsize=16,
                fontweight="bold",
            )
            ax.grid(axis="y", alpha=0.3)

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            path = self._get_chart_path("06_infrastructure_summary_bar.png")
            fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            return path

        except Exception as e:
            self.logger.warning(f"Could not plot infrastructure summary: {e}")
            return None

    def _plot_salary_histogram(self, vacancies: pd.DataFrame) -> Optional[str]:
        """Plot salary distribution histogram."""
        salaries = vacancies[vacancies["salary_min"] > 0]["salary_min"].dropna()
        if salaries.empty:
            return None

        fig, ax = plt.subplots(figsize=(12, 8))
        n, bins, patches = ax.hist(
            salaries,
            bins=30,
            edgecolor="black",
            alpha=0.7,
            color="steelblue",
            rwidth=0.9,
        )

        cmap = plt.cm.RdYlGn_r
        for i, patch in enumerate(patches):
            patch.set_facecolor(cmap(i / len(patches)))

        ax.axvline(
            salaries.mean(),
            color="red",
            linestyle="dashed",
            linewidth=2,
            label=f"Средняя: {salaries.mean():.0f} руб.",
        )
        ax.axvline(
            salaries.median(),
            color="blue",
            linestyle="dashed",
            linewidth=2,
            label=f"Медианная: {salaries.median():.0f} руб.",
        )

        ax.set_xlabel("Зарплата (руб.)", fontsize=12)
        ax.set_ylabel("Количество вакансий", fontsize=12)
        ax.set_title(
            f"Распределение зарплат в вакансиях\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.legend(loc="upper right", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        ax.xaxis.set_major_formatter(FuncFormatter(format_large_number))

        path = self._get_chart_path("07_salary_histogram.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_vacancies_by_city(self, vacancies: pd.DataFrame) -> Optional[str]:
        """Plot vacancies distribution by city."""
        if "city" not in vacancies.columns:
            return None

        city_counts = vacancies["city"].value_counts()
        if city_counts.empty:
            return None

        # Group small cities as "Другие"
        total = city_counts.sum()
        main = city_counts[city_counts / total >= 0.03]
        others = city_counts[city_counts / total < 0.03]

        if len(others) > 0:
            result = pd.concat([main, pd.Series({"Другие города": others.sum()})])
        else:
            result = main

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(result)))

        def autopct(pct):
            return f"{pct:.1f}%" if pct > 5 else ""

        ax.pie(
            result.values,
            labels=result.index,
            autopct=autopct,
            colors=colors,
            startangle=90,
            textprops={"fontsize": 12},
        )

        ax.set_title(
            f"Распределение вакансий по городам\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        path = self._get_chart_path("08_vacancies_by_city.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_salary_by_city(self, vacancies: pd.DataFrame) -> Optional[str]:
        """Plot average salary by city."""
        if "city" not in vacancies.columns or "salary_min" not in vacancies.columns:
            return None

        filtered = vacancies[(vacancies["salary_min"] > 0) & vacancies["city"].notna()]
        if filtered.empty:
            return None

        city_salary = (
            filtered.groupby("city")["salary_min"].mean().sort_values(ascending=False)
        )

        city_counts = filtered.groupby("city").size()
        city_salary = city_salary[city_counts >= 3]

        if city_salary.empty:
            city_salary = (
                filtered.groupby("city")["salary_min"]
                .mean()
                .sort_values(ascending=False)
            )

        if city_salary.empty:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = plt.cm.RdYlGn(np.linspace(0.1, 0.9, len(city_salary)))
        bars = ax.barh(
            range(len(city_salary)),
            city_salary.values,
            color=colors,
            edgecolor="black",
            linewidth=0.5,
        )

        ax.set_yticks(range(len(city_salary)))
        ax.set_yticklabels(city_salary.index, fontsize=11)
        ax.set_xlabel("Средняя зарплата (руб.)", fontsize=12)
        ax.set_title(
            f"Средняя зарплата по городам\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.xaxis.set_major_formatter(FuncFormatter(format_large_number))

        for bar, val in zip(bars, city_salary.values):
            ax.text(
                bar.get_width() + 1000,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}".replace(",", " "),
                va="center",
                fontsize=10,
                fontweight="bold",
            )

        ax.grid(axis="x", alpha=0.3)

        path = self._get_chart_path("09_salary_by_city_barh.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_category_by_object_type(self, matched_df: pd.DataFrame) -> Optional[str]:
        """Plot category distribution by object type."""
        if matched_df.empty or "vacancy_category" not in matched_df.columns:
            return None

        matched = matched_df.copy()
        matched["vacancy_category"] = matched["vacancy_category"].fillna("Не указано")

        pivot = (
            pd.crosstab(
                matched["object_type"], matched["vacancy_category"], normalize="index"
            )
            * 100
        )

        if pivot.shape[1] > 10:
            top_cols = pivot.sum().sort_values(ascending=False).head(8).index
            pivot = pivot[top_cols]

        fig, ax = plt.subplots(figsize=(14, 8))
        pivot.T.plot(
            kind="bar", ax=ax, colormap="Set2", edgecolor="black", linewidth=0.5
        )

        ax.set_xlabel("Категория профессии", fontsize=12)
        ax.set_ylabel("Доля вакансий (%)", fontsize=12)
        ax.set_title(
            f"Категории профессий по типам объектов\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.legend(title="Тип объекта", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(axis="y", alpha=0.3)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

        plt.tight_layout()
        path = self._get_chart_path("10_category_by_object_type.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_top_objects_by_vacancies(
        self, objects_agg_df: pd.DataFrame, top_n: int = 20
    ) -> Optional[str]:
        """Plot top objects by vacancies count."""
        if objects_agg_df.empty or "vacancies_count" not in objects_agg_df.columns:
            return None

        top_objects = objects_agg_df.nlargest(top_n, "vacancies_count")

        if top_objects.empty:
            return None

        top_objects["display_name"] = top_objects["object_name"].astype(str)

        fig, ax = plt.subplots(figsize=(14, 10))
        colors = plt.cm.plasma(np.linspace(0.1, 0.9, len(top_objects)))
        bars = ax.barh(
            range(len(top_objects)),
            top_objects["vacancies_count"].values,
            color=colors,
            edgecolor="black",
            linewidth=0.5,
        )

        ax.set_yticks(range(len(top_objects)))
        ax.set_yticklabels(top_objects["display_name"].values, fontsize=9)
        ax.set_xlabel("Количество вакансий", fontsize=12)
        ax.set_title(
            f"Топ-{top_n} объектов по количеству вакансий\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.invert_yaxis()

        for bar, val in zip(bars, top_objects["vacancies_count"].values):
            ax.text(
                bar.get_width() + 2,
                bar.get_y() + bar.get_height() / 2,
                str(val),
                va="center",
                fontsize=9,
                fontweight="bold",
            )

        ax.grid(axis="x", alpha=0.3)

        path = self._get_chart_path(f"11_top_{top_n}_objects_by_vacancies.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_top_objects_by_salary(
        self, objects_agg_df: pd.DataFrame, top_n: int = 20
    ) -> Optional[str]:
        """Plot top objects by average salary."""
        if objects_agg_df.empty or "avg_salary" not in objects_agg_df.columns:
            return None

        objects_with_salary = objects_agg_df[objects_agg_df["avg_salary"] > 0].nlargest(
            top_n, "avg_salary"
        )

        if objects_with_salary.empty:
            return None

        objects_with_salary["display_name"] = objects_with_salary["object_name"].astype(
            str
        )

        fig, ax = plt.subplots(figsize=(14, 10))
        colors = plt.cm.RdYlGn(np.linspace(0.1, 0.9, len(objects_with_salary)))
        bars = ax.barh(
            range(len(objects_with_salary)),
            objects_with_salary["avg_salary"].values,
            color=colors,
            edgecolor="black",
            linewidth=0.5,
        )

        ax.set_yticks(range(len(objects_with_salary)))
        ax.set_yticklabels(objects_with_salary["display_name"].values, fontsize=9)
        ax.set_xlabel("Средняя зарплата (руб.)", fontsize=12)
        ax.set_title(
            f"Топ-{top_n} объектов по средней зарплате\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.xaxis.set_major_formatter(FuncFormatter(format_large_number))
        ax.invert_yaxis()

        for bar, val in zip(bars, objects_with_salary["avg_salary"].values):
            ax.text(
                bar.get_width() + 1000,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}".replace(",", " "),
                va="center",
                fontsize=9,
                fontweight="bold",
            )

        ax.grid(axis="x", alpha=0.3)

        path = self._get_chart_path(f"12_top_{top_n}_objects_by_salary.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_experience_pie(self, vacancies: pd.DataFrame) -> Optional[str]:
        """Plot experience requirements as pie chart."""
        exp_counts = vacancies["experience"].value_counts().sort_index()
        if exp_counts.empty:
            return None

        grouped = {}
        for exp, count in exp_counts.items():
            if exp == 0:
                grouped["Без опыта"] = grouped.get("Без опыта", 0) + count
            elif exp <= 1:
                grouped["До 1 года"] = grouped.get("До 1 года", 0) + count
            elif exp <= 3:
                grouped["1-3 года"] = grouped.get("1-3 года", 0) + count
            elif exp <= 5:
                grouped["3-5 лет"] = grouped.get("3-5 лет", 0) + count
            else:
                grouped["Более 5 лет"] = grouped.get("Более 5 лет", 0) + count

        result = pd.Series(grouped)[pd.Series(grouped) > 0]

        if result.empty:
            return None

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set2(np.linspace(0, 1, len(result)))

        def autopct(pct):
            return f"{pct:.1f}%" if pct > 8 else ""

        ax.pie(
            result.values,
            labels=result.index,
            autopct=autopct,
            colors=colors,
            startangle=90,
        )

        ax.set_title(
            f"Требования к опыту работы в вакансиях\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )

        path = self._get_chart_path("13_experience_distribution_pie.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_education_pie(self, vacancies: pd.DataFrame) -> Optional[str]:
        """Plot education requirements as pie chart."""
        edu_counts = vacancies["education"].value_counts()
        edu_counts = edu_counts[edu_counts.index.notna()]

        if edu_counts.empty:
            return None

        edu_mapping = {
            "Не указано": "Не указано",
            "Tребования не предъявляются": "Без требований",
            "Высшее образование — бакалавриат": "Высшее",
            "Высшее образование — специалитет, магистратура": "Высшее",
            "Среднее профессиональное образование": "Среднее профессиональное",
            "Общее образование": "Общее",
        }

        edu_counts.index = edu_counts.index.map(lambda x: edu_mapping.get(x, x))
        edu_counts = edu_counts.groupby(level=0).sum()

        total = edu_counts.sum()
        main_cat = edu_counts[edu_counts / total >= 0.05]
        others = edu_counts[edu_counts / total < 0.05]

        if len(others) > 0:
            result = pd.concat([main_cat, pd.Series({"Остальные": others.sum()})])
        else:
            result = main_cat

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set1(np.linspace(0, 1, len(result)))

        def autopct(pct):
            return f"{pct:.1f}%" if pct > 5 else ""

        ax.pie(
            result.values,
            labels=result.index,
            autopct=autopct,
            colors=colors,
            startangle=90,
        )

        ax.set_title(
            f"Требования к образованию в вакансиях\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )

        path = self._get_chart_path("14_education_distribution_pie.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_salary_boxplot_by_category(
        self, vacancies: pd.DataFrame, top_n: int = 15
    ) -> Optional[str]:
        """Plot salary boxplot by category."""
        if "category" not in vacancies.columns:
            return None

        filtered = vacancies[
            (vacancies["salary_min"] > 0) & (vacancies["category"].notna())
        ]

        if filtered.empty:
            return None

        top_cats = filtered["category"].value_counts().head(top_n).index
        filtered_top = filtered[filtered["category"].isin(top_cats)]

        fig, ax = plt.subplots(figsize=(14, 10))
        filtered_top.boxplot(column="salary_min", by="category", ax=ax)

        ax.set_title(
            f"Распределение зарплат по категориям профессий\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
        )
        ax.set_xlabel("Категория профессии", fontsize=12)
        ax.set_ylabel("Зарплата (руб.)", fontsize=12)
        ax.yaxis.set_major_formatter(FuncFormatter(format_large_number))
        plt.suptitle("")
        plt.xticks(rotation=45, ha="right")

        plt.tight_layout()
        path = self._get_chart_path("15_salary_boxplot_by_category.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    def _plot_matched_vacancies_by_object_type(
        self, matched_df: pd.DataFrame
    ) -> Optional[str]:
        """Plot matched vacancies distribution by object type."""
        if matched_df.empty or "object_type" not in matched_df.columns:
            return None

        object_type_counts = matched_df["object_type"].value_counts()

        if object_type_counts.empty:
            return None

        type_ru = {
            "bank": "Банки",
            "industry": "Производства",
            "beauty": "Салоны красоты",
            "retail": "Магазины",
        }

        labels = [type_ru.get(t, t) for t in object_type_counts.index]

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(object_type_counts)))

        def autopct(pct):
            return f"{pct:.1f}%" if pct > 5 else ""

        ax.pie(
            object_type_counts.values,
            labels=labels,
            autopct=autopct,
            colors=colors,
            startangle=90,
            textprops={"fontsize": 12},
        )

        ax.set_title(
            f"Распределение связанных вакансий по типам объектов\n{self.region_name}",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        path = self._get_chart_path("16_matched_vacancies_by_object_type.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path
