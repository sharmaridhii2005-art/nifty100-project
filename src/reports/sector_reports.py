"""
Sprint 5 - Sector Report Generator

Generates one PDF report for every broad sector.

Database:
    db/nifty100.db

Input tables:
    companies
    sectors
    financial_ratios

Output:
    reports/sectors/

Expected:
    10 sector PDF reports
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "sectors"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONSTANTS
# ============================================================

EXPECTED_COMPANIES = 92

EXPECTED_SECTORS = 10



# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_text(value) -> str:
    """
    Convert database values into clean printable text.
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    text = str(value)

    # Remove escaped/newline characters
    text = text.replace("\\n", " ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def safe_number(value, decimals=2):
    """
    Convert numeric values into display-friendly strings.
    """

    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except Exception:
        pass

    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return "N/A"


def safe_filename(value) -> str:
    """
    Make a value safe for Windows filenames.
    """

    value = clean_text(value)

    value = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        value
    )

    value = re.sub(
        r"\s+",
        "_",
        value
    )

    return value.strip("_") or "sector"


def numeric_series(df, column):
    """
    Return a numeric pandas Series.
    """

    if column not in df.columns:
        return pd.Series(
            dtype="float64"
        )

    return pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# DATABASE
# ============================================================

def load_database():
    """
    Load all required database tables.
    """

    print()
    print("=" * 60)
    print("Sprint 5 - Sector Report Generator")
    print("=" * 60)

    print()
    print("Database :", DB_PATH)
    print("Output   :", OUTPUT_DIR)

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    conn = sqlite3.connect(
        DB_PATH
    )

    try:

        companies = pd.read_sql_query(
            "SELECT * FROM companies",
            conn
        )

        sectors = pd.read_sql_query(
            "SELECT * FROM sectors",
            conn
        )

        ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios",
            conn
        )

    finally:

        conn.close()

    return companies, sectors, ratios


# ============================================================
# VALIDATE DATABASE
# ============================================================

def validate_tables(
    companies,
    sectors,
    ratios
):
    """
    Validate expected tables and columns.
    """

    print()
    print("Companies table :", len(companies))
    print("Sectors table   :", len(sectors))
    print("Ratios records  :", len(ratios))

    print()
    print("Companies columns:")
    print(companies.columns.tolist())

    print()
    print("Sectors columns:")
    print(sectors.columns.tolist())

    print()
    print("Ratio columns:")
    print(ratios.columns.tolist())

    # --------------------------------------------------------
    # Companies
    # --------------------------------------------------------

    if "id" not in companies.columns:

        raise ValueError(
            "companies table must contain 'id'."
        )

    # --------------------------------------------------------
    # Sectors
    # --------------------------------------------------------

    required_sector_columns = [
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
    ]

    missing = [
        col
        for col in required_sector_columns
        if col not in sectors.columns
    ]

    if missing:

        raise ValueError(
            "sectors table is missing columns: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # Ratios
    # --------------------------------------------------------

    if "company_id" not in ratios.columns:

        raise ValueError(
            "financial_ratios table must contain "
            "'company_id'."
        )

    # --------------------------------------------------------
    # Normalize IDs
    # --------------------------------------------------------

    companies["id"] = (
        companies["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    sectors["company_id"] = (
        sectors["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    ratios["company_id"] = (
        ratios["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Expected company universe
    # --------------------------------------------------------

    company_ids = set(
        companies["id"]
    )

    sector_company_ids = set(
        sectors["company_id"]
    )

    matched = company_ids & sector_company_ids

    print()
    print(
        "Companies with sector mapping :",
        len(matched)
    )

    if len(companies) != EXPECTED_COMPANIES:

        print(
            "WARNING: Expected",
            EXPECTED_COMPANIES,
            "companies but found",
            len(companies)
        )

    if len(matched) < EXPECTED_COMPANIES:

        missing_ids = sorted(
            company_ids - sector_company_ids
        )

        print(
            "WARNING: Companies without sector mapping:"
        )

        print(
            missing_ids
        )


# ============================================================
# PREPARE SECTOR DATA
# ============================================================

def prepare_sector_data(
    companies,
    sectors,
    ratios
):
    """
    Merge company, sector and ratio information.

    Important:
    The sectors table uses 'broad_sector'.
    There is no generic 'sector' column in the
    actual database schema.
    """

    companies_clean = companies.copy()

    sectors_clean = sectors.copy()

    ratios_clean = ratios.copy()

    # --------------------------------------------------------
    # Normalize IDs
    # --------------------------------------------------------

    companies_clean["company_id"] = (
        companies_clean["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    sectors_clean["company_id"] = (
        sectors_clean["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    ratios_clean["company_id"] = (
        ratios_clean["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Clean sector names
    # --------------------------------------------------------

    sectors_clean["broad_sector"] = (
        sectors_clean["broad_sector"]
        .apply(clean_text)
    )

    sectors_clean["sub_sector"] = (
        sectors_clean["sub_sector"]
        .apply(clean_text)
    )

    # --------------------------------------------------------
    # One sector record per company
    # --------------------------------------------------------

    sectors_clean = (
        sectors_clean
        .drop_duplicates(
            subset=["company_id"],
            keep="first"
        )
    )

    # --------------------------------------------------------
    # Latest ratio record per company
    #
    # financial_ratios contains historical records.
    # We need one current/latest record for the
    # sector comparison table.
    # --------------------------------------------------------

    if "year" in ratios_clean.columns:

        ratios_clean["_year_sort"] = (
            ratios_clean["year"]
            .astype(str)
            .str.extract(
                r"(\d{4})"
            )[0]
        )

        ratios_clean["_year_sort"] = pd.to_numeric(
            ratios_clean["_year_sort"],
            errors="coerce"
        )

        ratios_latest = (
            ratios_clean
            .sort_values(
                [
                    "company_id",
                    "_year_sort"
                ],
                na_position="first"
            )
            .groupby(
                "company_id",
                as_index=False
            )
            .tail(1)
        )

    else:

        ratios_latest = (
            ratios_clean
            .drop_duplicates(
                subset=["company_id"],
                keep="last"
            )
        )

    # --------------------------------------------------------
    # Merge companies + sectors
    # --------------------------------------------------------

    data = companies_clean.merge(
        sectors_clean[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
                "index_weight_pct",
                "market_cap_category",
            ]
        ],
        on="company_id",
        how="inner"
    )

    # --------------------------------------------------------
    # Merge latest ratios
    # --------------------------------------------------------

    data = data.merge(
        ratios_latest,
        on="company_id",
        how="left",
        suffixes=(
            "",
            "_ratio"
        )
    )

    # --------------------------------------------------------
    # Remove duplicate ratio columns if present
    # --------------------------------------------------------

    duplicate_columns = [
        col
        for col in data.columns
        if col.endswith("_ratio")
        and col[:-6] in data.columns
    ]

    for col in duplicate_columns:

        data.drop(
            columns=[col],
            inplace=True
        )

    # --------------------------------------------------------
    # Final cleanup
    # --------------------------------------------------------

    data["company_name_clean"] = (
        data["company_name"]
        .apply(clean_text)
    )

    data["broad_sector"] = (
        data["broad_sector"]
        .replace(
            "",
            "Unknown"
        )
    )

    return data


# ============================================================
# SELECT KPI COLUMNS
# ============================================================

def get_kpi_columns(data):
    """
    Select available KPI columns from financial_ratios.
    """

    candidates = [
        (
            "return_on_equity_pct",
            "ROE (%)"
        ),
        (
            "net_profit_margin_pct",
            "Net Profit Margin (%)"
        ),
        (
            "operating_profit_margin_pct",
            "Operating Margin (%)"
        ),
        (
            "debt_to_equity",
            "Debt / Equity"
        ),
        (
            "interest_coverage",
            "Interest Coverage"
        ),
        (
            "asset_turnover",
            "Asset Turnover"
        ),
        (
            "free_cash_flow_cr",
            "Free Cash Flow (₹ Cr)"
        ),
        (
            "capex_cr",
            "CapEx (₹ Cr)"
        ),
        (
            "earnings_per_share",
            "EPS"
        ),
        (
            "book_value_per_share",
            "Book Value / Share"
        ),
        (
            "dividend_payout_ratio_pct",
            "Dividend Payout (%)"
        ),
    ]

    available = []

    for column, label in candidates:

        if column in data.columns:

            available.append(
                (
                    column,
                    label
                )
            )

    return available


# ============================================================
# SECTOR SUMMARY
# ============================================================

def calculate_sector_summary(
    sector_df
):
    """
    Calculate median / average sector statistics.
    """

    summary = {}

    kpis = get_kpi_columns(
        sector_df
    )

    for column, label in kpis:

        values = numeric_series(
            sector_df,
            column
        ).dropna()

        if len(values) == 0:

            summary[column] = None

        else:

            summary[column] = values.median()

    return summary


# ============================================================
# BEST / WORST COMPANY
# ============================================================

def find_best_worst(
    sector_df,
    column="return_on_equity_pct"
):
    """
    Find best and worst company using ROE.
    """

    if column not in sector_df.columns:

        return None, None

    temp = sector_df[
        [
            "company_id",
            "company_name_clean",
            column,
        ]
    ].copy()

    temp[column] = pd.to_numeric(
        temp[column],
        errors="coerce"
    )

    temp = temp.dropna(
        subset=[column]
    )

    if temp.empty:

        return None, None

    best = temp.loc[
        temp[column].idxmax()
    ]

    worst = temp.loc[
        temp[column].idxmin()
    ]

    return best, worst


# ============================================================
# PDF STYLES
# ============================================================

def get_styles():

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SectorTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "SectorSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    heading_style = ParagraphStyle(
        "SectorHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=8,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "SectorNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        spaceAfter=4,
    )

    small_style = ParagraphStyle(
        "SectorSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
    )

    return (
        title_style,
        subtitle_style,
        heading_style,
        normal_style,
        small_style,
    )


# ============================================================
# TABLE STYLE
# ============================================================

def apply_table_style(
    table,
    header=True
):

    commands = [
        (
            "FONTNAME",
            (0, 0),
            (-1, -1),
            "Helvetica"
        ),
        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            7
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            colors.grey
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4
        ),
    ]

    if header:

        commands.extend(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#1F4E78"
                    )
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
            ]
        )

    table.setStyle(
        TableStyle(commands)
    )

    return table


# ============================================================
# CREATE SECTOR PDF
# ============================================================

def create_sector_pdf(
    sector_name,
    sector_df,
    output_path
):
    """
    Create one PDF for one broad sector.
    """

    (
        title_style,
        subtitle_style,
        heading_style,
        normal_style,
        small_style,
    ) = get_styles()

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{sector_name} Sector Report",
        author="Nifty 100 Financial Intelligence Platform",
    )

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    story.append(
        Paragraph(
            f"{clean_text(sector_name)}",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Nifty 100 Financial Intelligence Platform "
            "— Sector Report",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            f"Report Date: "
            f"{datetime.now().strftime('%d-%m-%Y')}",
            subtitle_style
        )
    )

    # ========================================================
    # SECTOR OVERVIEW
    # ========================================================

    story.append(
        Paragraph(
            "Sector Overview",
            heading_style
        )
    )

    company_count = len(
        sector_df
    )

    total_weight = numeric_series(
        sector_df,
        "index_weight_pct"
    ).sum()

    sub_sector_count = (
        sector_df["sub_sector"]
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    overview_data = [
        [
            "Sector",
            "Companies",
            "Sub-sectors",
            "Index Weight (%)",
        ],
        [
            clean_text(sector_name),
            str(company_count),
            str(sub_sector_count),
            safe_number(total_weight),
        ],
    ]

    overview_table = Table(
        overview_data,
        colWidths=[
            80 * mm,
            35 * mm,
            35 * mm,
            45 * mm,
        ]
    )

    apply_table_style(
        overview_table
    )

    story.append(
        overview_table
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    # ========================================================
    # MEDIAN KPI TABLE
    # ========================================================

    story.append(
        Paragraph(
            "Sector Median KPI Table",
            heading_style
        )
    )

    summary = calculate_sector_summary(
        sector_df
    )

    median_rows = [
        [
            "KPI",
            "Sector Median"
        ]
    ]

    for column, label in get_kpi_columns(
        sector_df
    ):

        median_rows.append(
            [
                label,
                safe_number(
                    summary.get(column)
                )
            ]
        )

    if len(median_rows) == 1:

        median_rows.append(
            [
                "No KPI data",
                "N/A"
            ]
        )

    median_table = Table(
        median_rows,
        colWidths=[
            100 * mm,
            50 * mm,
        ]
    )

    apply_table_style(
        median_table
    )

    story.append(
        median_table
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    # ========================================================
    # BEST / WORST
    # ========================================================

    story.append(
        Paragraph(
            "Best / Worst Company",
            heading_style
        )
    )

    best, worst = find_best_worst(
        sector_df
    )

    if best is not None:

        best_name = clean_text(
            best["company_name_clean"]
        )

        worst_name = clean_text(
            worst["company_name_clean"]
        )

        best_roe = safe_number(
            best["return_on_equity_pct"]
        )

        worst_roe = safe_number(
            worst["return_on_equity_pct"]
        )

        best_worst_rows = [
            [
                "Category",
                "Company",
                "ROE (%)",
            ],
            [
                "Best",
                f"{best['company_id']} - {best_name}",
                best_roe,
            ],
            [
                "Worst",
                f"{worst['company_id']} - {worst_name}",
                worst_roe,
            ],
        ]

    else:

        best_worst_rows = [
            [
                "Category",
                "Company",
                "ROE (%)",
            ],
            [
                "Data unavailable",
                "N/A",
                "N/A",
            ],
        ]

    best_worst_table = Table(
        best_worst_rows,
        colWidths=[
            35 * mm,
            120 * mm,
            35 * mm,
        ]
    )

    apply_table_style(
        best_worst_table
    )

    if len(best_worst_rows) >= 3:

        best_worst_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, 1),
                        colors.HexColor(
                            "#E2F0D9"
                        )
                    ),
                    (
                        "BACKGROUND",
                        (0, 2),
                        (-1, 2),
                        colors.HexColor(
                            "#FCE4D6"
                        )
                    ),
                ]
            )
        )

    story.append(
        best_worst_table
    )

    story.append(
        PageBreak()
    )

    # ========================================================
    # COMPANY LIST
    # ========================================================

    story.append(
        Paragraph(
            f"Companies in {clean_text(sector_name)}",
            heading_style
        )
    )

    company_rows = [
        [
            "Ticker",
            "Company",
            "Sub-sector",
            "Index Weight %",
            "ROE %",
            "NPM %",
            "OPM %",
            "D/E",
            "ICR",
            "FCF ₹Cr",
        ]
    ]

    display_df = sector_df.copy()

    # Sort by ROE where possible
    if "return_on_equity_pct" in display_df.columns:

        display_df["_roe_sort"] = numeric_series(
            display_df,
            "return_on_equity_pct"
        )

        display_df = display_df.sort_values(
            "_roe_sort",
            ascending=False,
            na_position="last"
        )

    for _, row in display_df.iterrows():

        ticker = clean_text(
            row.get("company_id")
        )

        company_name = clean_text(
            row.get("company_name_clean")
        )

        sub_sector = clean_text(
            row.get("sub_sector")
        )

        company_rows.append(
            [
                ticker,
                company_name[:42],
                sub_sector[:28],
                safe_number(
                    row.get(
                        "index_weight_pct"
                    )
                ),
                safe_number(
                    row.get(
                        "return_on_equity_pct"
                    )
                ),
                safe_number(
                    row.get(
                        "net_profit_margin_pct"
                    )
                ),
                safe_number(
                    row.get(
                        "operating_profit_margin_pct"
                    )
                ),
                safe_number(
                    row.get(
                        "debt_to_equity"
                    )
                ),
                safe_number(
                    row.get(
                        "interest_coverage"
                    )
                ),
                safe_number(
                    row.get(
                        "free_cash_flow_cr"
                    )
                ),
            ]
        )

    company_table = Table(
        company_rows,
        repeatRows=1,
        colWidths=[
            25 * mm,
            55 * mm,
            42 * mm,
            28 * mm,
            24 * mm,
            24 * mm,
            24 * mm,
            20 * mm,
            20 * mm,
            30 * mm,
        ]
    )

    apply_table_style(
        company_table
    )

    story.append(
        company_table
    )

    story.append(
        Spacer(
            1,
            10
        )
    )

    # ========================================================
    # SUB-SECTOR DISTRIBUTION
    # ========================================================

    story.append(
        Paragraph(
            "Sub-sector Distribution",
            heading_style
        )
    )

    sub_counts = (
        sector_df["sub_sector"]
        .replace(
            "",
            "Unknown"
        )
        .fillna("Unknown")
        .value_counts()
    )

    sub_rows = [
        [
            "Sub-sector",
            "Companies",
            "Share (%)",
        ]
    ]

    for sub_sector, count in sub_counts.items():

        percentage = (
            count / company_count * 100
            if company_count
            else 0
        )

        sub_rows.append(
            [
                clean_text(
                    sub_sector
                ),
                str(count),
                safe_number(
                    percentage
                ),
            ]
        )

    sub_table = Table(
        sub_rows,
        repeatRows=1,
        colWidths=[
            100 * mm,
            40 * mm,
            40 * mm,
        ]
    )

    apply_table_style(
        sub_table
    )

    story.append(
        sub_table
    )

    story.append(
        Spacer(
            1,
            10
        )
    )

    # ========================================================
    # DISCLAIMER
    # ========================================================

    story.append(
        Paragraph(
            "Note: Sector statistics are calculated from "
            "the financial ratios available in the project "
            "SQLite database. Median KPI values are used "
            "for sector comparison. This report is an "
            "analytical output and not investment advice.",
            small_style
        )
    )

    # ========================================================
    # BUILD
    # ========================================================

    document.build(
        story
    )


# ============================================================
# GENERATE ALL SECTOR REPORTS
# ============================================================

def generate_all_reports(
    data
):
    """
    Generate one PDF for every broad sector.
    """

    sectors = (
        data["broad_sector"]
        .dropna()
        .astype(str)
        .map(clean_text)
        .replace(
            "",
            "Unknown"
        )
        .unique()
        .tolist()
    )

    sectors = sorted(
        sectors,
        key=lambda x: x.lower()
    )

    print()
    print(
        "Sectors to generate :",
        len(sectors)
    )

    if len(sectors) != EXPECTED_SECTORS:

        print()
        print(
            "WARNING: Expected",
            EXPECTED_SECTORS,
            "broad sectors but found",
            len(sectors)
        )

        print(
            "Sectors found:"
        )

        for sector in sectors:

            print(
                " -",
                sector
            )

    generated = 0
    failed = 0

    print()

    report_date = datetime.now().strftime(
        "%Y%m%d"
    )

    for index, sector_name in enumerate(
        sectors,
        start=1
    ):

        sector_df = data[
            data["broad_sector"]
            .astype(str)
            .map(clean_text)
            == sector_name
        ].copy()

        filename = (
            f"{safe_filename(sector_name)}"
            f"_report_{report_date}.pdf"
        )

        output_path = (
            OUTPUT_DIR / filename
        )

        try:

            create_sector_pdf(
                sector_name,
                sector_df,
                output_path
            )

            size_kb = (
                output_path.stat().st_size
                / 1024
            )

            print(
                f"[{index:2d}/{len(sectors)}] "
                f"{sector_name:<30} "
                f"{size_kb:7.1f} KB  "
                f"{filename}"
            )

            generated += 1

        except Exception as exc:

            failed += 1

            print(
                f"[{index:2d}/{len(sectors)}] "
                f"{sector_name:<30} "
                f"FAILED"
            )

            print(
                "       Error:",
                repr(exc)
            )

    return generated, failed


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Load database
        # ----------------------------------------------------

        companies, sectors, ratios = (
            load_database()
        )

        # ----------------------------------------------------
        # Validate tables
        # ----------------------------------------------------

        validate_tables(
            companies,
            sectors,
            ratios
        )

        # ----------------------------------------------------
        # Prepare merged dataset
        # ----------------------------------------------------

        print()
        print(
            "Preparing sector data..."
        )

        data = prepare_sector_data(
            companies,
            sectors,
            ratios
        )

        print(
            "Prepared rows :",
            len(data)
        )

        print(
            "Unique companies :",
            data["company_id"].nunique()
        )

        print(
            "Unique broad sectors :",
            data["broad_sector"].nunique()
        )

        # ----------------------------------------------------
        # Generate PDFs
        # ----------------------------------------------------

        generated, failed = (
            generate_all_reports(
                data
            )
        )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print(
            "Sector Report Generation Completed"
        )
        print("=" * 60)

        print(
            "Generated :",
            generated
        )

        print(
            "Failed    :",
            failed
        )

        print(
            "Expected sectors :",
            EXPECTED_SECTORS
        )

        print(
            "Output    :",
            OUTPUT_DIR
        )

        print()

        if (
            generated == EXPECTED_SECTORS
            and failed == 0
        ):

            print(
                "SUCCESS: All 11 sector reports generated."
            )

        elif generated > 0:

            print(
                "WARNING: Some sector reports were not generated."
            )

        else:

            print(
                "ERROR: No sector reports were generated."
            )

    except Exception as exc:

        print()
        print("=" * 60)
        print(
            "SECTOR REPORT GENERATOR FAILED"
        )
        print("=" * 60)

        print(
            "Error:",
            repr(exc)
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()