"""
Sprint 6 - Day 37

Cluster profiling
Correlation heatmap
Sector-based outlier detection
Portfolio statistics
"""

from pathlib import Path
import sqlite3
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

CLUSTER_FILE = OUTPUT_DIR / "cluster_labels.csv"

OUTLIER_FILE = OUTPUT_DIR / "outlier_report.csv"
PORTFOLIO_FILE = OUTPUT_DIR / "portfolio_stats.csv"

CORRELATION_FILE = REPORTS_DIR / "correlation_heatmap.png"


# ============================================================
# DATABASE
# ============================================================


def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================================
# YEAR
# ============================================================


def extract_year(value):
    """Extract four-digit year from strings such as Mar 2022."""
    
    if pd.isna(value):
        return np.nan

    match = re.search(r"(19|20)\d{2}", str(value))

    if match:
        return int(match.group())

    return np.nan


# ============================================================
# CAGR
# ============================================================


def calculate_cagr(start_value, end_value, years=5):
    """
    Calculate CAGR.

    CAGR is undefined when either endpoint is
    zero or negative.
    """

    if pd.isna(start_value) or pd.isna(end_value):
        return np.nan

    if start_value <= 0 or end_value <= 0:
        return np.nan

    return (
        (end_value / start_value) ** (1 / years) - 1
    ) * 100


# ============================================================
# LOAD CLUSTERS
# ============================================================


def load_clusters():

    if not CLUSTER_FILE.exists():
        raise FileNotFoundError(
            f"Missing cluster file: {CLUSTER_FILE}"
        )

    df = pd.read_csv(CLUSTER_FILE)

    print(
        f"Cluster rows loaded: {len(df)}"
    )

    print(
        f"Unique companies: "
        f"{df['company_id'].nunique()}"
    )

    return df


# ============================================================
# LOAD DATABASE DATA
# ============================================================


def load_database():

    conn = get_connection()

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            free_cash_flow_cr,
            capex_cr,
            earnings_per_share,
            book_value_per_share
        FROM financial_ratios
        """,
        conn,
    )

    profit_loss = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales
        FROM profitandloss
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector,
            sub_sector
        FROM sectors
        """,
        conn,
    )

    conn.close()

    return ratios, profit_loss, sectors


# ============================================================
# LATEST RATIOS
# ============================================================


def get_latest_ratios(ratios):

    df = ratios.copy()

    df["year_num"] = df["year"].apply(
        extract_year
    )

    df = df.dropna(
        subset=["company_id", "year_num"]
    )

    # Remove duplicate company/year rows.
    df = (
        df
        .sort_values(
            ["company_id", "year_num"]
        )
        .drop_duplicates(
            ["company_id", "year_num"],
            keep="last",
        )
    )

    # Latest available year per company.
    latest = (
        df
        .sort_values(
            ["company_id", "year_num"]
        )
        .drop_duplicates(
            "company_id",
            keep="last",
        )
    )

    return latest


# ============================================================
# REVENUE CAGR
# ============================================================


def calculate_revenue_cagr(profit_loss):

    df = profit_loss.copy()

    df["year_num"] = df["year"].apply(
        extract_year
    )

    df["sales"] = pd.to_numeric(
        df["sales"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "company_id",
            "year_num",
            "sales",
        ]
    )

    df = (
        df
        .sort_values(
            ["company_id", "year_num"]
        )
        .drop_duplicates(
            ["company_id", "year_num"],
            keep="last",
        )
    )

    records = []

    for company_id, group in df.groupby(
        "company_id"
    ):

        group = group.sort_values(
            "year_num"
        )

        if len(group) < 6:
            continue

        latest = group.iloc[-1]

        target_year = (
            latest["year_num"] - 5
        )

        previous = group[
            group["year_num"] == target_year
        ]

        if previous.empty:
            continue

        previous = previous.iloc[-1]

        cagr = calculate_cagr(
            previous["sales"],
            latest["sales"],
            5,
        )

        records.append(
            {
                "company_id": company_id,
                "revenue_cagr_5yr": cagr,
            }
        )

    return pd.DataFrame(records)


# ============================================================
# FCF CAGR
# ============================================================


def calculate_fcf_cagr(ratios):

    df = ratios.copy()

    df["year_num"] = df["year"].apply(
        extract_year
    )

    df["free_cash_flow_cr"] = pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "company_id",
            "year_num",
            "free_cash_flow_cr",
        ]
    )

    df = (
        df
        .sort_values(
            ["company_id", "year_num"]
        )
        .drop_duplicates(
            ["company_id", "year_num"],
            keep="last",
        )
    )

    records = []

    for company_id, group in df.groupby(
        "company_id"
    ):

        group = group.sort_values(
            "year_num"
        )

        if len(group) < 6:
            continue

        latest = group.iloc[-1]

        target_year = (
            latest["year_num"] - 5
        )

        previous = group[
            group["year_num"] == target_year
        ]

        if previous.empty:
            continue

        previous = previous.iloc[-1]

        cagr = calculate_cagr(
            previous["free_cash_flow_cr"],
            latest["free_cash_flow_cr"],
            5,
        )

        records.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": cagr,
            }
        )

    return pd.DataFrame(records)


# ============================================================
# BUILD COMPLETE DATASET
# ============================================================


def build_dataset():

    print("\nLoading database...")

    ratios, profit_loss, sectors = (
        load_database()
    )

    latest = get_latest_ratios(
        ratios
    )

    revenue_cagr = calculate_revenue_cagr(
        profit_loss
    )

    fcf_cagr = calculate_fcf_cagr(
        ratios
    )

    print(
        "Revenue CAGR companies:",
        revenue_cagr["company_id"].nunique()
        if not revenue_cagr.empty
        else 0,
    )

    print(
        "FCF CAGR companies:",
        fcf_cagr["company_id"].nunique()
        if not fcf_cagr.empty
        else 0,
    )

    # Merge Revenue CAGR
    latest = latest.merge(
        revenue_cagr,
        on="company_id",
        how="left",
    )

    # Merge FCF CAGR
    latest = latest.merge(
        fcf_cagr,
        on="company_id",
        how="left",
    )

    # Merge sectors
    latest = latest.merge(
        sectors,
        on="company_id",
        how="left",
    )

    return latest


# ============================================================
# CLUSTER PROFILE
# ============================================================


CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def create_cluster_profile(
    clusters,
    financial_data,
):

    data = clusters.merge(
        financial_data,
        on="company_id",
        how="left",
    )

    print(
        "\nCompanies after cluster/data merge:",
        data["company_id"].nunique(),
    )

    profile = (
        data
        .groupby(
            [
                "cluster_id",
                "cluster_name",
            ]
        )[CLUSTER_FEATURES]
        .agg(
            ["mean", "median"]
        )
        .round(2)
    )

    return data, profile


# ============================================================
# CORRELATION HEATMAP
# ============================================================


CORRELATION_KPIS = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "capex_cr",
    "earnings_per_share",
    "book_value_per_share",
]


def create_correlation_heatmap(
    financial_data
):

    available = [
        column
        for column in CORRELATION_KPIS
        if column in financial_data.columns
    ]

    correlation = (
        financial_data[available]
        .corr(method="pearson")
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(12, 9)
    )

    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        linewidths=0.5,
    )

    plt.title(
        "Pearson Correlation Matrix - Nifty 100 KPIs"
    )

    plt.tight_layout()

    plt.savefig(
        CORRELATION_FILE,
        dpi=150,
    )

    plt.close()

    return correlation


# ============================================================
# OUTLIER DETECTION
# ============================================================


OUTLIER_METRICS = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "capex_cr",
    "earnings_per_share",
    "book_value_per_share",
]


def create_outlier_report(
    financial_data
):

    df = financial_data.copy()

    records = []

    for metric in OUTLIER_METRICS:

        if metric not in df.columns:
            continue

        for sector, group in df.groupby(
            "broad_sector",
            dropna=False,
        ):

            values = pd.to_numeric(
                group[metric],
                errors="coerce",
            )

            mean = values.mean()
            std = values.std(
                ddof=0
            )

            if pd.isna(std) or std == 0:
                continue

            z_scores = (
                (values - mean) / std
            )

            for index, z_score in (
                z_scores.items()
            ):

                if pd.isna(z_score):
                    continue

                if abs(z_score) > 3:

                    row = group.loc[index]

                    records.append(
                        {
                            "company_id":
                                row["company_id"],

                            "broad_sector":
                                sector,

                            "metric":
                                metric,

                            "value":
                                row[metric],

                            "z_score":
                                z_score,

                            "threshold":
                                3,
                        }
                    )

    report = pd.DataFrame(
        records,
        columns=[
            "company_id",
            "broad_sector",
            "metric",
            "value",
            "z_score",
            "threshold",
        ],
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report.to_csv(
        OUTLIER_FILE,
        index=False,
    )

    return report


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================


def create_portfolio_stats(
    financial_data
):

    available = [
        metric
        for metric in CORRELATION_KPIS
        if metric in financial_data.columns
    ]

    records = []

    for metric in available:

        values = pd.to_numeric(
            financial_data[metric],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        records.append(
            {
                "KPI": metric,
                "P10": values.quantile(0.10),
                "P25": values.quantile(0.25),
                "P50": values.quantile(0.50),
                "P75": values.quantile(0.75),
                "P90": values.quantile(0.90),
                "Mean": values.mean(),
                "Std": values.std(),
            }
        )

    result = pd.DataFrame(
        records
    ).set_index("KPI")

    result = result.round(4)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        PORTFOLIO_FILE
    )

    return result


# ============================================================
# MAIN
# ============================================================


def main():

    print("=" * 70)

    print(
        "SPRINT 6 - DAY 37"
    )

    print(
        "CLUSTER PROFILING + CORRELATION + OUTLIERS + PORTFOLIO"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Load clusters
    # --------------------------------------------------------

    print(
        "\n1. Loading cluster assignments..."
    )

    clusters = load_clusters()

    # --------------------------------------------------------
    # Build financial dataset
    # --------------------------------------------------------

    print(
        "\n2. Building financial dataset..."
    )

    financial_data = build_dataset()

    print(
        "Financial companies:",
        financial_data["company_id"].nunique(),
    )

    # --------------------------------------------------------
    # Cluster profile
    # --------------------------------------------------------

    print(
        "\n3. Creating cluster profile..."
    )

    merged, profile = (
        create_cluster_profile(
            clusters,
            financial_data,
        )
    )

    print(
        "\nCLUSTER PROFILE"
    )

    print(profile)

    # --------------------------------------------------------
    # Correlation
    # --------------------------------------------------------

    print(
        "\n4. Creating correlation heatmap..."
    )

    correlation = (
        create_correlation_heatmap(
            financial_data
        )
    )

    print(
        f"Saved: {CORRELATION_FILE}"
    )

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    print(
        "\n5. Detecting sector outliers..."
    )

    outliers = (
        create_outlier_report(
            financial_data
        )
    )

    print(
        "Outliers found:",
        len(outliers),
    )

    print(
        f"Saved: {OUTLIER_FILE}"
    )

    # --------------------------------------------------------
    # Portfolio statistics
    # --------------------------------------------------------

    print(
        "\n6. Creating portfolio statistics..."
    )

    portfolio = (
        create_portfolio_stats(
            financial_data
        )
    )

    print(
        "\nPORTFOLIO STATISTICS"
    )

    print(portfolio)

    print(
        f"\nSaved: {PORTFOLIO_FILE}"
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "DAY 37 COMPLETED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()