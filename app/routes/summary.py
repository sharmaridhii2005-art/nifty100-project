from fastapi import APIRouter
import pandas as pd

from app.utils.database import get_connection

router = APIRouter(
    prefix="/companies",
    tags=["Company Summary"]
)


@router.get("/{company_id}/summary")
def get_company_summary(company_id: str):

    company_id = company_id.upper()

    conn = get_connection()

    # Company information
    company = conn.execute("""
        SELECT
            id,
            company_name,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        WHERE id = ?
    """, (company_id,)).fetchone()

    # Sector information
    sector = conn.execute("""
        SELECT
            broad_sector,
            sub_sector,
            index_weight_pct,
            market_cap_category
        FROM sectors
        WHERE company_id = ?
    """, (company_id,)).fetchone()

    # Latest financial ratio
    ratio = conn.execute("""
        SELECT
            year,
            return_on_equity_pct,
            debt_to_equity,
            operating_profit_margin_pct,
            free_cash_flow_cr,
            cash_from_operations_cr
        FROM financial_ratios
        WHERE company_id = ?
       ORDER BY
    CAST(
        CASE
            WHEN year LIKE '% %'
            THEN substr(year, instr(year, ' ') + 1)
            ELSE year
        END AS INTEGER
    ) DESC
LIMIT 1
    """, (company_id,)).fetchone()

    conn.close()

    if company is None:
        return {
            "error": "Company not found",
            "company_id": company_id
        }

    # Cluster information
    cluster_df = pd.read_csv("output/cluster_labels.csv")

    cluster = cluster_df[
        cluster_df["company_id"].str.upper() == company_id
    ]

    cluster_data = None

    if not cluster.empty:
        cluster_data = cluster.iloc[0].to_dict()

    # Valuation information
    valuation_df = pd.read_csv("output/valuation_flags.csv")

    valuation = valuation_df[
        valuation_df["company_id"].str.upper() == company_id
    ]

    valuation_data = None

    if not valuation.empty:
        valuation_data = valuation.iloc[0].to_dict()

    # Outlier information
    outlier_df = pd.read_csv("output/outlier_report.csv")

    outliers = outlier_df[
        outlier_df["company_id"].str.upper() == company_id
    ]

    outlier_data = outliers.to_dict(orient="records")

    return {
        "company": dict(company),
        "sector": dict(sector) if sector else None,
        "latest_ratio": dict(ratio) if ratio else None,
        "cluster": cluster_data,
        "valuation": valuation_data,
        "outliers": outlier_data
    }