"""
Sprint 5 - Day 31
Cash Flow Intelligence Module

Outputs:
    output/cashflow_intelligence.xlsx
    output/distress_alerts.csv

The database has:
    companies.id                  -> company identifier
    cashflow.company_id
    profitandloss.company_id
    balancesheet.company_id
    financial_ratios.company_id

This script always uses the companies table as the
master list so that all 92 companies are represented.
"""

import os
import re
import sqlite3
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
# ============================================================
# KPI FUNCTIONS
# ============================================================

def free_cash_flow(cfo, capex):
    return cfo + capex


def cfo_quality_score(cfo, net_profit):
    if net_profit == 0:
        return "Accrual Risk"

    ratio = (cfo / net_profit) * 100

    if ratio >= 100:
        return "High Quality"
    elif ratio >= 50:
        return "Moderate"
    else:
        return "Accrual Risk"


def capex_intensity(capex, cfo):
    if cfo == 0:
        return 0.0, "Insufficient Data"

    value = abs(capex) / abs(cfo) * 100

    if value < 5:
        label = "Low"
    elif value <= 15:
        label = "Moderate"
    else:
        label = "High"

    return round(value, 2), label


def fcf_conversion_rate(fcf, net_profit):
    if net_profit == 0:
        return 0.0

    return round((fcf / net_profit) * 100, 2)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DB_PATH = os.path.join(
    BASE_DIR,
    "db",
    "nifty100.db"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

INTELLIGENCE_FILE = os.path.join(
    OUTPUT_DIR,
    "cashflow_intelligence.xlsx"
)

DISTRESS_FILE = os.path.join(
    OUTPUT_DIR,
    "distress_alerts.csv"
)


# ============================================================
# CONSTANTS
# ============================================================

EXPECTED_COMPANIES = 92


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_columns(df):
    """
    Remove accidental whitespace and backslashes from
    column names.
    """

    df = df.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace("\\", "", regex=False)
    )

    return df


def clean_company_id(value):
    """
    Normalize company IDs.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def numeric(series):
    """
    Safely convert a pandas Series to numeric.
    """

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def parse_year(value):
    """
    Convert different year formats into a sortable integer.

    Examples:

        Mar-13    -> 2013
        Mar-14    -> 2014
        Dec 2012  -> 2012
        2018      -> 2018
        FY2020    -> 2020
    """

    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    if not text:
        return np.nan

    # Four digit year
    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group())

    # Two digit year
    match = re.search(r"\b(\d{2})\b", text)

    if match:

        yy = int(match.group(1))

        if yy <= 30:
            return 2000 + yy

        return 1900 + yy

    return np.nan


def prepare_year(df):
    """
    Add normalized sort_year column.
    """

    df = df.copy()

    if "year" not in df.columns:
        df["sort_year"] = np.nan
        return df

    df["sort_year"] = df["year"].apply(parse_year)

    return df


def safe_mean(values):
    """
    Mean ignoring NaN.
    """

    values = pd.to_numeric(
        pd.Series(values),
        errors="coerce"
    )

    values = values.dropna()

    if len(values) == 0:
        return np.nan

    return float(values.mean())


def safe_last(series):
    """
    Return latest non-null value.
    """

    series = pd.to_numeric(
        series,
        errors="coerce"
    )

    series = series.dropna()

    if len(series) == 0:
        return np.nan

    return float(series.iloc[-1])


def safe_cagr(start, end, years):
    """
    CAGR calculation.

    Returns NaN where calculation is not meaningful.
    """

    if pd.isna(start) or pd.isna(end):
        return np.nan

    if pd.isna(years) or years <= 0:
        return np.nan

    if start == 0:
        return np.nan

    # CAGR requires positive base and positive ending value
    if start > 0 and end > 0:

        try:
            return (
                (end / start) ** (1 / years) - 1
            ) * 100

        except Exception:
            return np.nan

    return np.nan


# ============================================================
# DATABASE LOADING
# ============================================================

def load_database():

    print()
    print("--------------------------------")
    print("Loading database")
    print("--------------------------------")

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)

    try:

        # ----------------------------------------------------
        # MASTER COMPANY TABLE
        # ----------------------------------------------------

        companies = pd.read_sql(
            "SELECT * FROM companies",
            conn
        )

        companies = clean_columns(companies)

        print(
            "Companies table:",
            len(companies)
        )

        print(
            "Companies columns:",
            companies.columns.tolist()
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # companies table uses `id`, NOT `company_id`
        # ----------------------------------------------------

        if "id" not in companies.columns:
            raise RuntimeError(
                "companies table does not contain `id`."
            )

        companies = companies.rename(
            columns={
                "id": "company_id"
            }
        )

        companies["company_id"] = (
            companies["company_id"]
            .apply(clean_company_id)
        )

        companies = companies[
            companies["company_id"].notna()
        ].copy()

        # Remove duplicates
        companies = companies.drop_duplicates(
            subset=["company_id"]
        )

        # ----------------------------------------------------
        # SECTORS
        # ----------------------------------------------------

        try:

            sectors = pd.read_sql(
                "SELECT * FROM sectors",
                conn
            )

            sectors = clean_columns(sectors)

        except Exception:

            sectors = pd.DataFrame()

        # ----------------------------------------------------
        # CASHFLOW
        # ----------------------------------------------------

        cashflow = pd.read_sql(
            "SELECT * FROM cashflow",
            conn
        )

        cashflow = clean_columns(cashflow)

        # ----------------------------------------------------
        # PROFIT & LOSS
        # ----------------------------------------------------

        profit_loss = pd.read_sql(
            "SELECT * FROM profitandloss",
            conn
        )

        profit_loss = clean_columns(profit_loss)

        # ----------------------------------------------------
        # BALANCE SHEET
        # ----------------------------------------------------

        balance_sheet = pd.read_sql(
            "SELECT * FROM balancesheet",
            conn
        )

        balance_sheet = clean_columns(balance_sheet)

        # ----------------------------------------------------
        # FINANCIAL RATIOS
        # ----------------------------------------------------

        ratios = pd.read_sql(
            "SELECT * FROM financial_ratios",
            conn
        )

        ratios = clean_columns(ratios)

    finally:

        conn.close()

    # ========================================================
    # NORMALIZE COMPANY IDs
    # ========================================================

    for df in [
        cashflow,
        profit_loss,
        balance_sheet,
        ratios
    ]:

        if "company_id" in df.columns:

            df["company_id"] = (
                df["company_id"]
                .apply(clean_company_id)
            )

    # ========================================================
    # NORMALIZE YEARS
    # ========================================================

    cashflow = prepare_year(cashflow)

    profit_loss = prepare_year(profit_loss)

    balance_sheet = prepare_year(balance_sheet)

    ratios = prepare_year(ratios)

    # ========================================================
    # REMOVE INVALID COMPANY IDs
    # ========================================================

    cashflow = cashflow[
        cashflow["company_id"].notna()
    ].copy()

    profit_loss = profit_loss[
        profit_loss["company_id"].notna()
    ].copy()

    balance_sheet = balance_sheet[
        balance_sheet["company_id"].notna()
    ].copy()

    ratios = ratios[
        ratios["company_id"].notna()
    ].copy()

    print(
        "Cashflow companies after filter:",
        cashflow["company_id"].nunique()
    )

    print(
        "Profit/Loss companies after filter:",
        profit_loss["company_id"].nunique()
    )

    print(
        "Balance Sheet companies after filter:",
        balance_sheet["company_id"].nunique()
    )

    print(
        "Financial Ratio companies after filter:",
        ratios["company_id"].nunique()
    )

    return (
        companies,
        sectors,
        cashflow,
        profit_loss,
        balance_sheet,
        ratios
    )


# ============================================================
# CFO QUALITY
# ============================================================

def calculate_cfo_quality(
    company_id,
    cashflow,
    profit_loss
):

    cfo = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    pnl = profit_loss[
        profit_loss["company_id"] == company_id
    ].copy()

    if cfo.empty or pnl.empty:

        return (
            np.nan,
            "Insufficient Data"
        )

    # --------------------------------------------------------
    # CFO
    # --------------------------------------------------------

    if "operating_activity" not in cfo.columns:
        return (
            np.nan,
            "Insufficient Data"
        )

    # --------------------------------------------------------
    # NET PROFIT
    # --------------------------------------------------------

    if "net_profit" not in pnl.columns:
        return (
            np.nan,
            "Insufficient Data"
        )

    cfo_small = cfo[
        [
            "sort_year",
            "operating_activity"
        ]
    ].copy()

    pnl_small = pnl[
        [
            "sort_year",
            "net_profit"
        ]
    ].copy()

    cfo_small["operating_activity"] = numeric(
        cfo_small["operating_activity"]
    )

    pnl_small["net_profit"] = numeric(
        pnl_small["net_profit"]
    )

    # --------------------------------------------------------
    # Merge using normalized year
    # --------------------------------------------------------

    merged = pd.merge(
        cfo_small,
        pnl_small,
        on="sort_year",
        how="inner"
    )

    if merged.empty:
        return (
            np.nan,
            "Insufficient Data"
        )

    # Remove invalid PAT
    merged = merged[
        merged["net_profit"].notna()
    ].copy()

    merged = merged[
        merged["net_profit"] != 0
    ].copy()

    if merged.empty:
        return (
            np.nan,
            "Insufficient Data"
        )

    # --------------------------------------------------------
    # CFO / PAT
    # --------------------------------------------------------

    merged["cfo_pat_ratio"] = (
        merged["operating_activity"]
        / merged["net_profit"]
    )

    merged = merged.replace(
        [np.inf, -np.inf],
        np.nan
    )

    merged = merged.dropna(
        subset=["cfo_pat_ratio"]
    )

    # Latest five years
    merged = merged.sort_values(
        "sort_year"
    ).tail(5)

    if merged.empty:
        return (
            np.nan,
            "Insufficient Data"
        )

    score = safe_mean(
        merged["cfo_pat_ratio"]
    )

    if pd.isna(score):
        label = "Insufficient Data"

    elif score > 1.0:
        label = "High Quality"

    elif score >= 0.5:
        label = "Moderate"

    else:
        label = "Accrual Risk"

    return score, label


# ============================================================
# CAPEX INTENSITY
# ============================================================

def calculate_capex_intensity(
    company_id,
    cashflow,
    profit_loss
):

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    pnl = profit_loss[
        profit_loss["company_id"] == company_id
    ].copy()

    if cf.empty or pnl.empty:
        return (
            np.nan,
            "Insufficient Data"
        )

    if "investing_activity" not in cf.columns:
        return (
            np.nan,
            "Insufficient Data"
        )

    if "sales" not in pnl.columns:
        return (
            np.nan,
            "Insufficient Data"
        )

    cf_small = cf[
        [
            "sort_year",
            "investing_activity"
        ]
    ].copy()

    pnl_small = pnl[
        [
            "sort_year",
            "sales"
        ]
    ].copy()

    cf_small["investing_activity"] = numeric(
        cf_small["investing_activity"]
    )

    pnl_small["sales"] = numeric(
        pnl_small["sales"]
    )

    merged = pd.merge(
        cf_small,
        pnl_small,
        on="sort_year",
        how="inner"
    )

    merged = merged[
        merged["sales"].notna()
    ].copy()

    merged = merged[
        merged["sales"] != 0
    ].copy()

    if merged.empty:
        return (
            np.nan,
            "Insufficient Data"
        )

    # Investing activity is normally negative for capex.
    merged["capex_intensity"] = (
        merged["investing_activity"].abs()
        / merged["sales"].abs()
        * 100
    )

    merged = merged.replace(
        [np.inf, -np.inf],
        np.nan
    )

    merged = merged.dropna(
        subset=["capex_intensity"]
    )

    if merged.empty:
        return (
            np.nan,
            "Insufficient Data"
        )

    latest = merged.sort_values(
        "sort_year"
    ).iloc[-1]

    value = float(
        latest["capex_intensity"]
    )

    if value < 3:
        label = "Asset Light"

    elif value <= 8:
        label = "Moderate"

    else:
        label = "Capital Intensive"

    return value, label


# ============================================================
# DISTRESS SIGNAL
# ============================================================

def calculate_distress(
    company_id,
    cashflow,
    profit_loss
):

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    if cf.empty:
        return (
            False,
            np.nan,
            np.nan,
            np.nan
        )

    cf = cf.sort_values(
        "sort_year"
    )

    latest = cf.iloc[-1]

    cfo = numeric(
        pd.Series(
            [latest.get("operating_activity")]
        )
    ).iloc[0]

    cff = numeric(
        pd.Series(
            [latest.get("financing_activity")]
        )
    ).iloc[0]

    # Latest net profit
    pnl = profit_loss[
        profit_loss["company_id"] == company_id
    ].copy()

    latest_profit = np.nan

    if not pnl.empty:

        pnl = pnl.sort_values(
            "sort_year"
        )

        latest_profit = numeric(
            pd.Series(
                [pnl.iloc[-1].get("net_profit")]
            )
        ).iloc[0]

    flag = (
        pd.notna(cfo)
        and pd.notna(cff)
        and cfo < 0
        and cff > 0
    )

    return (
        bool(flag),
        cfo,
        cff,
        latest_profit
    )


# ============================================================
# DELEVERAGING
# ============================================================

def calculate_deleveraging(
    company_id,
    cashflow,
    balance_sheet
):

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    bs = balance_sheet[
        balance_sheet["company_id"] == company_id
    ].copy()

    if cf.empty or bs.empty:
        return False

    if "financing_activity" not in cf.columns:
        return False

    if "borrowings" not in bs.columns:
        return False

    cf = cf.sort_values(
        "sort_year"
    )

    bs = bs.sort_values(
        "sort_year"
    )

    # Latest financing cash flow
    latest_cf = cf.iloc[-1]

    cff = numeric(
        pd.Series(
            [latest_cf.get("financing_activity")]
        )
    ).iloc[0]

    if pd.isna(cff):
        return False

    # Need latest two balance sheet years
    bs = bs[
        bs["borrowings"].notna()
    ].copy()

    if len(bs) < 2:
        return False

    previous = numeric(
        pd.Series(
            [bs.iloc[-2]["borrowings"]]
        )
    ).iloc[0]

    latest = numeric(
        pd.Series(
            [bs.iloc[-1]["borrowings"]]
        )
    ).iloc[0]

    if pd.isna(previous) or pd.isna(latest):
        return False

    # CFF < 0 and borrowings declining
    return bool(
        cff < 0
        and latest < previous
    )


# ============================================================
# FCF CAGR
# ============================================================

def calculate_fcf_cagr(
    company_id,
    cashflow
):

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    if cf.empty:
        return np.nan

    if "net_cash_flow" not in cf.columns:
        return np.nan

    cf = cf.sort_values(
        "sort_year"
    )

    cf = cf[
        cf["sort_year"].notna()
    ].copy()

    cf["net_cash_flow"] = numeric(
        cf["net_cash_flow"]
    )

    cf = cf[
        cf["net_cash_flow"].notna()
    ].copy()

    if len(cf) < 2:
        return np.nan

    # Last five years
    recent = cf.tail(5)

    if len(recent) < 2:
        return np.nan

    start = float(
        recent.iloc[0]["net_cash_flow"]
    )

    end = float(
        recent.iloc[-1]["net_cash_flow"]
    )

    years = (
        recent.iloc[-1]["sort_year"]
        - recent.iloc[0]["sort_year"]
    )

    return safe_cagr(
        start,
        end,
        years
    )


# ============================================================
# FCF CONVERSION
# ============================================================

def calculate_fcf_conversion(
    company_id,
    cashflow,
    profit_loss
):

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    pnl = profit_loss[
        profit_loss["company_id"] == company_id
    ].copy()

    if cf.empty or pnl.empty:
        return np.nan

    cf_small = cf[
        [
            "sort_year",
            "operating_activity",
            "investing_activity"
        ]
    ].copy()

    pnl_small = pnl[
        [
            "sort_year",
            "net_profit"
        ]
    ].copy()

    cf_small["operating_activity"] = numeric(
        cf_small["operating_activity"]
    )

    cf_small["investing_activity"] = numeric(
        cf_small["investing_activity"]
    )

    pnl_small["net_profit"] = numeric(
        pnl_small["net_profit"]
    )

    merged = pd.merge(
        cf_small,
        pnl_small,
        on="sort_year",
        how="inner"
    )

    if merged.empty:
        return np.nan

    merged = merged.sort_values(
        "sort_year"
    )

    latest = merged.iloc[-1]

    cfo = latest["operating_activity"]
    cfi = latest["investing_activity"]
    profit = latest["net_profit"]

    if pd.isna(cfo) or pd.isna(cfi):
        return np.nan

    if pd.isna(profit) or profit == 0:
        return np.nan

    # FCF = CFO + CFI
    fcf = cfo + cfi

    conversion = (
        fcf / profit
    ) * 100

    if not np.isfinite(conversion):
        return np.nan

    return float(conversion)


# ============================================================
# CAPITAL ALLOCATION
# ============================================================

def calculate_capital_allocation(
    company_id,
    cashflow,
    balance_sheet,
    profit_loss
):

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    bs = balance_sheet[
        balance_sheet["company_id"] == company_id
    ].copy()

    pnl = profit_loss[
        profit_loss["company_id"] == company_id
    ].copy()

    if cf.empty:
        return "Insufficient Data"

    cf = cf.sort_values(
        "sort_year"
    )

    latest_cf = cf.iloc[-1]

    cfo = numeric(
        pd.Series(
            [latest_cf.get("operating_activity")]
        )
    ).iloc[0]

    cfi = numeric(
        pd.Series(
            [latest_cf.get("investing_activity")]
        )
    ).iloc[0]

    cff = numeric(
        pd.Series(
            [latest_cf.get("financing_activity")]
        )
    ).iloc[0]

    # --------------------------------------------------------
    # Distress
    # --------------------------------------------------------

    if (
        pd.notna(cfo)
        and pd.notna(cff)
        and cfo < 0
        and cff > 0
    ):
        return "Distress Signal"

    # --------------------------------------------------------
    # Financing / deleveraging
    # --------------------------------------------------------

    deleveraging = calculate_deleveraging(
        company_id,
        cashflow,
        balance_sheet
    )

    if deleveraging:
        return "Deleveraging"

    # --------------------------------------------------------
    # Reinvestor
    # --------------------------------------------------------

    if (
        pd.notna(cfo)
        and pd.notna(cfi)
        and cfo > 0
        and cfi < 0
    ):

        return "Reinvestor"

    # --------------------------------------------------------
    # Cash Distributor
    # --------------------------------------------------------

    if (
        pd.notna(cfo)
        and pd.notna(cff)
        and cfo > 0
        and cff < 0
    ):

        return "Cash Distributor"

    # --------------------------------------------------------
    # Growth Financed
    # --------------------------------------------------------

    if (
        pd.notna(cfo)
        and pd.notna(cfi)
        and pd.notna(cff)
        and cfo > 0
        and cfi < 0
        and cff > 0
    ):

        return "Growth Financed"

    # --------------------------------------------------------
    # Self Funded
    # --------------------------------------------------------

    if (
        pd.notna(cfo)
        and pd.notna(cfi)
        and cfo > 0
        and cfi >= 0
    ):

        return "Self Funded"

    # --------------------------------------------------------
    # Capital Raised
    # --------------------------------------------------------

    if (
        pd.notna(cff)
        and cff > 0
    ):

        return "Capital Raised"

    # --------------------------------------------------------
    # Neutral
    # --------------------------------------------------------

    if (
        pd.notna(cfo)
        and cfo >= 0
    ):

        return "Neutral"

    return "Insufficient Data"


# ============================================================
# SECTOR LOOKUP
# ============================================================

def build_sector_map(
    companies,
    sectors
):

    result = companies[
        ["company_id"]
    ].copy()

    result["sector"] = "Unknown"

    if sectors.empty:
        return result

    sectors = sectors.copy()

    # --------------------------------------------------------
    # Find company ID column
    # --------------------------------------------------------

    possible_company_columns = [
        "company_id",
        "id"
    ]

    sector_company_col = None

    for col in possible_company_columns:

        if col in sectors.columns:

            sector_company_col = col
            break

    if sector_company_col is None:
        return result

    sectors = sectors.rename(
        columns={
            sector_company_col: "company_id"
        }
    )

    sectors["company_id"] = (
        sectors["company_id"]
        .apply(clean_company_id)
    )

    # --------------------------------------------------------
    # Find sector column
    # --------------------------------------------------------

    possible_sector_columns = [
        "broad_sector",
        "sector",
        "sector_name"
    ]

    sector_col = None

    for col in possible_sector_columns:

        if col in sectors.columns:

            sector_col = col
            break

    if sector_col is None:
        return result

    sector_map = sectors[
        [
            "company_id",
            sector_col
        ]
    ].drop_duplicates(
        subset=["company_id"]
    )

    sector_map = sector_map.rename(
        columns={
            sector_col: "sector"
        }
    )

    result = result.drop(
        columns=["sector"]
    )

    result = result.merge(
        sector_map,
        on="company_id",
        how="left"
    )

    result["sector"] = (
        result["sector"]
        .fillna("Unknown")
    )

    return result


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_cashflow_intelligence():

    print()
    print("---")
    print("## Cash Flow Intelligence Started")
    print("---")
    print()

    (
        companies,
        sectors,
        cashflow,
        profit_loss,
        balance_sheet,
        ratios
    ) = load_database()

    # ========================================================
    # MASTER COMPANY LIST
    # ========================================================

    master = companies[
        ["company_id"]
    ].copy()

    sector_map = build_sector_map(
        companies,
        sectors
    )

    master = master.merge(
        sector_map,
        on="company_id",
        how="left",
        suffixes=("", "_sector")
    )

    if "sector_sector" in master.columns:

        master["sector"] = (
            master["sector_sector"]
            .fillna(master["sector"])
        )

        master = master.drop(
            columns=["sector_sector"]
        )

    master["sector"] = (
        master["sector"]
        .fillna("Unknown")
    )

    # ========================================================
    # CALCULATE FOR EVERY COMPANY
    # ========================================================

    results = []

    distress_rows = []

    print()
    print(
        "Generating intelligence for:",
        len(master),
        "companies"
    )
    print()

    for index, row in master.iterrows():

        company_id = row["company_id"]

        sector = row["sector"]

        # ----------------------------------------------------
        # CFO QUALITY
        # ----------------------------------------------------

        cfo_score, cfo_label = calculate_cfo_quality(
            company_id,
            cashflow,
            profit_loss
        )

        # ----------------------------------------------------
        # CAPEX
        # ----------------------------------------------------

        capex_pct, capex_label = calculate_capex_intensity(
            company_id,
            cashflow,
            profit_loss
        )

        # ----------------------------------------------------
        # FCF CAGR
        # ----------------------------------------------------

        fcf_cagr = calculate_fcf_cagr(
            company_id,
            cashflow
        )

        # ----------------------------------------------------
        # FCF CONVERSION
        # ----------------------------------------------------

        fcf_conversion = calculate_fcf_conversion(
            company_id,
            cashflow,
            profit_loss
        )

        # ----------------------------------------------------
        # DISTRESS
        # ----------------------------------------------------

        (
            distress_flag,
            latest_cfo,
            latest_cff,
            latest_profit
        ) = calculate_distress(
            company_id,
            cashflow,
            profit_loss
        )

        # ----------------------------------------------------
        # DELEVERAGING
        # ----------------------------------------------------

        deleveraging_flag = calculate_deleveraging(
            company_id,
            cashflow,
            balance_sheet
        )

        # ----------------------------------------------------
        # CAPITAL ALLOCATION
        # ----------------------------------------------------

        capital_allocation_label = (
            calculate_capital_allocation(
                company_id,
                cashflow,
                balance_sheet,
                profit_loss
            )
        )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        results.append(
            {
                "company_id": company_id,
                "sector": sector,
                "cfo_quality_score": cfo_score,
                "cfo_quality_label": cfo_label,
                "capex_intensity_pct": capex_pct,
                "capex_label": capex_label,
                "fcf_cagr_5yr": fcf_cagr,
                "fcf_conversion_pct": fcf_conversion,
                "distress_flag": distress_flag,
                "deleveraging_flag": deleveraging_flag,
                "capital_allocation_label": capital_allocation_label
            }
        )

        # ----------------------------------------------------
        # DISTRESS ALERT
        # ----------------------------------------------------

        if distress_flag:

            distress_rows.append(
                {
                    "company_id": company_id,
                    "sector": sector,
                    "CFO": latest_cfo,
                    "CFF": latest_cff,
                    "latest_net_profit": latest_profit
                }
            )

    # ========================================================
    # DATAFRAME
    # ========================================================

    result = pd.DataFrame(
        results
    )

    # ========================================================
    # FORCE EXACT COLUMN ORDER
    # ========================================================

    required_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label"
    ]

    result = result[
        required_columns
    ]

    # ========================================================
    # SORT
    # ========================================================

    result = result.sort_values(
        "company_id"
    ).reset_index(
        drop=True
    )

    # ========================================================
    # SAVE EXCEL
    # ========================================================

    result.to_excel(
        INTELLIGENCE_FILE,
        index=False
    )

    # ========================================================
    # DISTRESS CSV
    # ========================================================

    distress_df = pd.DataFrame(
        distress_rows
    )

    if distress_df.empty:

        distress_df = pd.DataFrame(
            columns=[
                "company_id",
                "sector",
                "CFO",
                "CFF",
                "latest_net_profit"
            ]
        )

    distress_df = distress_df.sort_values(
        "company_id"
    ).reset_index(
        drop=True
    )

    distress_df.to_csv(
        DISTRESS_FILE,
        index=False
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    actual_companies = result[
        "company_id"
    ].nunique()

    missing_companies = (
        set(master["company_id"])
        -
        set(result["company_id"])
    )

    extra_companies = (
        set(result["company_id"])
        -
        set(master["company_id"])
    )

    print()
    print("--------------------------------")
    print("Cash Flow Intelligence Completed")
    print("--------------------------------")
    print()

    print(
        "Companies generated :",
        actual_companies
    )

    print(
        "Expected companies  :",
        EXPECTED_COMPANIES
    )

    print()

    print(
        "Created :",
        INTELLIGENCE_FILE
    )

    print(
        "Created :",
        DISTRESS_FILE
    )

    print()

    # --------------------------------------------------------
    # Missing company check
    # --------------------------------------------------------

    if missing_companies:

        print(
            "WARNING: Missing companies:"
        )

        print(
            sorted(missing_companies)
        )

    # --------------------------------------------------------
    # Extra company check
    # --------------------------------------------------------

    if extra_companies:

        print(
            "WARNING: Extra companies:"
        )

        print(
            sorted(extra_companies)
        )

    # --------------------------------------------------------
    # Expected count
    # --------------------------------------------------------

    if actual_companies == EXPECTED_COMPANIES:

        print(
            "SUCCESS: Exactly 92 companies generated."
        )

    else:

        print(
            "WARNING:",
            f"Expected {EXPECTED_COMPANIES}",
            f"but generated {actual_companies}"
        )

    print()

    # ========================================================
    # SUMMARY
    # ========================================================

    print("--------------------------------")
    print("Summary")
    print("--------------------------------")
    print()

    print(
        "High Quality CFO:",
        (
            result["cfo_quality_label"]
            == "High Quality"
        ).sum()
    )

    print(
        "Moderate CFO:",
        (
            result["cfo_quality_label"]
            == "Moderate"
        ).sum()
    )

    print(
        "Accrual Risk:",
        (
            result["cfo_quality_label"]
            == "Accrual Risk"
        ).sum()
    )

    print(
        "Distress Signals:",
        int(
            result["distress_flag"].sum()
        )
    )

    print(
        "Deleveraging:",
        int(
            result["deleveraging_flag"].sum()
        )
    )

    print()

    print(
        "Capital Allocation Distribution:"
    )

    print(
        result[
            "capital_allocation_label"
        ].value_counts()
    )

    print()

    return result


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    generate_cashflow_intelligence()