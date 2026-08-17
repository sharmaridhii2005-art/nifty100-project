"""
Sprint 6 - Day 36
KMeans clustering for Nifty 100 companies.
"""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

CLUSTER_OUTPUT = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_OUTPUT = REPORTS_DIR / "elbow_plot.png"


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------


def get_connection():
    """Return a connection to the project SQLite database."""
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------


def load_data():
    """Load company, ratio, P&L and cash-flow data."""
    conn = get_connection()

    companies = pd.read_sql_query(
        """
        SELECT
            id,
            company_name
        FROM companies
        """,
        conn,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            free_cash_flow_cr
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

    cashflow = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity
        FROM cashflow
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT *
        FROM sectors
        """,
        conn,
    )

    conn.close()

    return companies, ratios, profit_loss, cashflow, sectors


# ---------------------------------------------------------------------
# Year utilities
# ---------------------------------------------------------------------


def extract_year(value):
    """Extract a four-digit year from a year string."""
    if pd.isna(value):
        return np.nan

    text = str(value)

    import re

    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group())

    return np.nan


# ---------------------------------------------------------------------
# CAGR calculation
# ---------------------------------------------------------------------


def calculate_cagr(start_value, end_value, years=5):
    """Calculate CAGR when both endpoint values are positive."""
    if pd.isna(start_value) or pd.isna(end_value):
        return np.nan

    if start_value <= 0 or end_value <= 0:
        return np.nan

    return ((end_value / start_value) ** (1 / years) - 1) * 100


def calculate_revenue_cagr(profit_loss):
    """Calculate five-year revenue CAGR for each company."""
    df = profit_loss.copy()

    df["year_num"] = df["year"].apply(extract_year)
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")

    df = df.dropna(subset=["company_id", "year_num", "sales"])

    df = (
        df.sort_values(["company_id", "year_num"])
        .drop_duplicates(["company_id", "year_num"], keep="last")
    )

    records = []

    for company_id, group in df.groupby("company_id"):
        group = group.sort_values("year_num")

        if len(group) < 6:
            continue

        latest = group.iloc[-1]

        target_year = latest["year_num"] - 5

        previous = group[group["year_num"] == target_year]

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


def calculate_fcf_cagr(ratios):
    """Calculate five-year FCF CAGR for each company."""
    df = ratios.copy()

    df["year_num"] = df["year"].apply(extract_year)
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
        df.sort_values(["company_id", "year_num"])
        .drop_duplicates(
            ["company_id", "year_num"],
            keep="last",
        )
    )

    records = []

    for company_id, group in df.groupby("company_id"):
        group = group.sort_values("year_num")

        if len(group) < 6:
            continue

        latest = group.iloc[-1]

        target_year = latest["year_num"] - 5

        previous = group[group["year_num"] == target_year]

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


# ---------------------------------------------------------------------
# Latest financial ratios
# ---------------------------------------------------------------------


def get_latest_ratios(ratios):
    """Return the latest financial ratio row for each company."""
    df = ratios.copy()

    df["year_num"] = df["year"].apply(extract_year)

    df = df.dropna(subset=["company_id", "year_num"])

    df = (
        df.sort_values(["company_id", "year_num"])
        .drop_duplicates("company_id", keep="last")
    )

    return df[
        [
            "company_id",
            "year_num",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
        ]
    ]


# ---------------------------------------------------------------------
# Sector mapping
# ---------------------------------------------------------------------


def prepare_sector_mapping(companies, sectors):
    """Create a company-to-sector mapping."""
    company_sector = None

    possible_sector_columns = [
        "sector",
        "broad_sector",
        "sector_name",
    ]

    for column in possible_sector_columns:
        if column in companies.columns:
            company_sector = column
            break

    if company_sector:
        mapping = companies[
            ["id", company_sector]
        ].rename(
            columns={
                "id": "company_id",
                company_sector: "broad_sector",
            }
        )

        return mapping

    possible_company_columns = [
        "company_id",
        "id",
    ]

    possible_sector_columns = [
        "sector",
        "broad_sector",
        "sector_name",
    ]

    company_column = next(
        (
            col
            for col in possible_company_columns
            if col in sectors.columns
        ),
        None,
    )

    sector_column = next(
        (
            col
            for col in possible_sector_columns
            if col in sectors.columns
        ),
        None,
    )

    if company_column and sector_column:
        return sectors[
            [company_column, sector_column]
        ].rename(
            columns={
                company_column: "company_id",
                sector_column: "broad_sector",
            }
        )

    return pd.DataFrame(
        columns=["company_id", "broad_sector"]
    )


# ---------------------------------------------------------------------
# Main dataset
# ---------------------------------------------------------------------


def build_clustering_dataset():
    """Build the five-feature clustering dataset."""
    (
        companies,
        ratios,
        profit_loss,
        cashflow,
        sectors,
    ) = load_data()

    latest_ratios = get_latest_ratios(ratios)

    revenue_cagr = calculate_revenue_cagr(
        profit_loss
    )

    fcf_cagr = calculate_fcf_cagr(
        ratios
    )

    sector_mapping = prepare_sector_mapping(
        companies,
        sectors,
    )

    df = latest_ratios.merge(
        revenue_cagr,
        on="company_id",
        how="left",
    )

    df = df.merge(
        fcf_cagr,
        on="company_id",
        how="left",
    )

    df = df.merge(
        sector_mapping,
        on="company_id",
        how="left",
    )

    return df


# ---------------------------------------------------------------------
# Sector median imputation
# ---------------------------------------------------------------------


FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def impute_sector_median(df):
    """Fill missing feature values using sector medians."""
    result = df.copy()

    for feature in FEATURES:
        sector_median = result.groupby(
            "broad_sector"
        )[feature].transform("median")

        result[feature] = result[feature].fillna(
            sector_median
        )

        # Fallback to overall median if a sector has
        # no usable value.
        result[feature] = result[feature].fillna(
            result[feature].median()
        )

    return result


# ---------------------------------------------------------------------
# Elbow plot
# ---------------------------------------------------------------------


def create_elbow_plot(X):
    """Create and save the KMeans elbow plot for k=2 through k=10."""
    inertias = []
    k_values = range(2, 11)

    for k in k_values:
        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10,
        )

        model.fit(X)

        inertias.append(model.inertia_)

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(figsize=(8, 5))

    plt.plot(
        list(k_values),
        inertias,
        marker="o",
    )

    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")

    plt.xticks(list(k_values))

    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        ELBOW_OUTPUT,
        dpi=150,
    )

    plt.close()


# ---------------------------------------------------------------------
# Cluster naming
# ---------------------------------------------------------------------


def assign_cluster_names(clustered):
    """Assign descriptive names based on cluster financial profiles."""
    profile = (
        clustered.groupby("cluster_id")[FEATURES]
        .mean()
    )

    names = {}

    # High ROE + high revenue growth + strong OPM
    quality_score = (
        profile["return_on_equity_pct"]
        + profile["revenue_cagr_5yr"]
        + profile["operating_profit_margin_pct"]
        - profile["debt_to_equity"]
    )

    quality_cluster = quality_score.idxmax()

    names[quality_cluster] = "High-Quality Compounders"

    remaining = [
        cluster
        for cluster in profile.index
        if cluster not in names
    ]

    # Highest growth
    growth_score = (
        profile.loc[remaining, "revenue_cagr_5yr"]
        + profile.loc[remaining, "fcf_cagr_5yr"]
    )

    growth_cluster = growth_score.idxmax()

    names[growth_cluster] = "Emerging Growth"

    remaining = [
        cluster
        for cluster in profile.index
        if cluster not in names
    ]

    # Highest debt / weakest quality
    distress_score = (
        profile.loc[remaining, "debt_to_equity"]
        - profile.loc[remaining, "return_on_equity_pct"]
    )

    distress_cluster = distress_score.idxmax()

    names[distress_cluster] = "Distressed or Turnaround"

    remaining = [
        cluster
        for cluster in profile.index
        if cluster not in names
    ]

    # Highest ROE among remaining
    defensive_cluster = profile.loc[
        remaining,
        "return_on_equity_pct",
    ].idxmax()

    names[defensive_cluster] = (
        "Defensive Dividend Payers"
    )

    remaining = [
        cluster
        for cluster in profile.index
        if cluster not in names
    ]

    if remaining:
        names[remaining[0]] = "Value Cyclicals"

    clustered["cluster_name"] = clustered[
        "cluster_id"
    ].map(names)

    return clustered


# ---------------------------------------------------------------------
# Run clustering
# ---------------------------------------------------------------------


def run_clustering():
    """Run the complete Sprint 6 Day 36 clustering workflow."""
    print("=" * 70)
    print("SPRINT 6 - DAY 36 - KMEANS CLUSTERING")
    print("=" * 70)

    df = build_clustering_dataset()

    print("\nInitial companies:", df["company_id"].nunique())

    missing_before = df[FEATURES].isna().sum()

    print("\nMissing values before imputation:")
    print(missing_before)

    df = impute_sector_median(df)

    missing_after = df[FEATURES].isna().sum()

    print("\nMissing values after imputation:")
    print(missing_after)

    # Remove duplicate companies if any exist.
    df = (
        df.sort_values("year_num")
        .drop_duplicates(
            "company_id",
            keep="last",
        )
    )

    # Keep companies with complete clustering features.
    df = df.dropna(subset=FEATURES)

    print(
        "\nCompanies used for clustering:",
        df["company_id"].nunique(),
    )

    X = df[FEATURES].astype(float)

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    print("\nStandardScaler applied.")

    # Elbow plot
    create_elbow_plot(X_scaled)

    print(
        f"\nElbow plot saved to: {ELBOW_OUTPUT}"
    )

    # Final KMeans
    model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=10,
    )

    cluster_ids = model.fit_predict(X_scaled)

    df["cluster_id"] = cluster_ids

    # Distance from assigned centroid
    distances = np.linalg.norm(
        X_scaled - model.cluster_centers_[cluster_ids],
        axis=1,
    )

    df["distance_from_centroid"] = distances

    # Descriptive names
    df = assign_cluster_names(df)

    # Final output
    output = df[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].sort_values(
        ["cluster_id", "company_id"]
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        CLUSTER_OUTPUT,
        index=False,
    )

    print(
        f"\nCluster labels saved to: {CLUSTER_OUTPUT}"
    )

    print("\nCluster counts:")
    print(
        output["cluster_name"].value_counts()
    )

    print("\nCluster preview:")
    print(output.head(10))

    print("\nCompleted successfully.")

    return output


if __name__ == "__main__":
    run_clustering()