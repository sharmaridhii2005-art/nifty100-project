"""
Sprint 5 - Company Tearsheet Generator

Generates 2-page PDF tearsheets for the official 92 companies
from the companies table.

Output:
    reports/tearsheets/<TICKER>_tearsheet.pdf

Requirements:
    - Official company universe comes ONLY from companies table.
    - Cash flow / P&L / balance sheet tables are used only as data sources.
    - Companies with fewer than 3 years of data are skipped.
    - PDF must contain 2 pages.
"""

import os
import sys
import sqlite3
import textwrap
from pathlib import Path

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

DB_PATH = ROOT_DIR / "db" / "nifty100.db"
OUTPUT_DIR = ROOT_DIR / "reports" / "tearsheets"
CHART_DIR = ROOT_DIR / "reports" / "tearsheet_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIG
# ============================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

NAVY = colors.HexColor("#102A43")
GREEN = colors.HexColor("#1B7F3A")
RED = colors.HexColor("#B42318")
LIGHT_GREY = colors.HexColor("#F3F4F6")
MID_GREY = colors.HexColor("#6B7280")
WHITE = colors.white
BLACK = colors.black


# ============================================================
# REPORTLAB STYLES
# ============================================================

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "TearsheetTitle",
    parent=styles["Title"],
    fontSize=18,
    leading=21,
    textColor=WHITE,
    alignment=TA_LEFT,
    spaceAfter=0,
)

SUBTITLE_STYLE = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontSize=8,
    leading=10,
    textColor=WHITE,
)

SECTION_STYLE = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontSize=11,
    leading=13,
    textColor=NAVY,
    spaceBefore=5,
    spaceAfter=5,
)

NORMAL_STYLE = ParagraphStyle(
    "NormalCustom",
    parent=styles["Normal"],
    fontSize=7.5,
    leading=9.5,
    textColor=BLACK,
)

SMALL_STYLE = ParagraphStyle(
    "Small",
    parent=styles["Normal"],
    fontSize=6.5,
    leading=8,
    textColor=BLACK,
)

PRO_STYLE = ParagraphStyle(
    "Pro",
    parent=styles["Normal"],
    fontSize=7.2,
    leading=9,
    textColor=GREEN,
    leftIndent=5,
)

CON_STYLE = ParagraphStyle(
    "Con",
    parent=styles["Normal"],
    fontSize=7.2,
    leading=9,
    textColor=RED,
    leftIndent=5,
)

CENTER_STYLE = ParagraphStyle(
    "Center",
    parent=styles["Normal"],
    fontSize=7,
    leading=8,
    alignment=TA_CENTER,
)


# ============================================================
# DATABASE
# ============================================================

def load_database():
    """
    Load all required Sprint 5 tables.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    print()
    print("--------------------------------")
    print("Loading database")
    print("--------------------------------")
    print(f"Database : {DB_PATH}")

    # --------------------------------------------------------
    # IMPORTANT:
    # Official universe is companies table.
    # Its 'id' column contains the ticker.
    # --------------------------------------------------------

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        ORDER BY id
        """,
        conn,
    )

    cashflow = pd.read_sql_query(
        """
        SELECT *
        FROM cashflow
        """,
        conn,
    )

    profitloss = pd.read_sql_query(
        """
        SELECT *
        FROM profitandloss
        """,
        conn,
    )

    balancesheet = pd.read_sql_query(
        """
        SELECT *
        FROM balancesheet
        """,
        conn,
    )

    financial_ratios = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        """,
        conn,
    )

    # --------------------------------------------------------
    # Pros / Cons
    # --------------------------------------------------------

    try:
        proscons = pd.read_csv(
            ROOT_DIR / "output" / "pros_cons_generated.csv"
        )
    except Exception:
        proscons = pd.DataFrame(
            columns=[
                "company_id",
                "type",
                "rule_id",
                "text",
                "confidence_pct",
            ]
        )

    # --------------------------------------------------------
    # Cash Flow Intelligence
    # --------------------------------------------------------

    try:
        intelligence = pd.read_excel(
            ROOT_DIR / "output" / "cashflow_intelligence.xlsx"
        )
    except Exception:
        intelligence = pd.DataFrame()

    conn.close()

    print(f"Official companies : {len(companies)}")
    print(f"Cashflow records   : {len(cashflow)}")
    print(f"Profit/Loss records: {len(profitloss)}")
    print(f"Balance records    : {len(balancesheet)}")
    print(f"Ratio records      : {len(financial_ratios)}")

    return (
        companies,
        cashflow,
        profitloss,
        balancesheet,
        financial_ratios,
        proscons,
        intelligence,
    )


# ============================================================
# YEAR PARSING
# ============================================================

def parse_year(value):
    """
    Convert values such as:
        Mar-13
        Mar 2017
        Dec 2012
        2023
    into a sortable numeric year.
    """

    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    # Four-digit year
    import re

    match = re.search(r"(19|20)\d{2}", value)

    if match:
        return int(match.group())

    # Two-digit year
    match = re.search(r"[-/ ](\d{2})$", value)

    if match:
        year = int(match.group(1))

        if year <= 50:
            return 2000 + year

        return 1900 + year

    return np.nan


# ============================================================
# DATA HELPERS
# ============================================================

def company_data(df, company_id):
    """
    Return rows for one company.
    """

    if df.empty or "company_id" not in df.columns:
        return pd.DataFrame()

    result = df[
        df["company_id"].astype(str).str.strip()
        == str(company_id).strip()
    ].copy()

    if "year" in result.columns:
        result["sort_year"] = result["year"].apply(parse_year)
        result = result.sort_values("sort_year")

    return result


def numeric_series(df, column):
    if df.empty or column not in df.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        df[column],
        errors="coerce"
    )


def latest_value(df, column, default=np.nan):
    if df.empty or column not in df.columns:
        return default

    temp = df.copy()

    if "sort_year" not in temp.columns and "year" in temp.columns:
        temp["sort_year"] = temp["year"].apply(parse_year)

    temp = temp.sort_values("sort_year")

    values = pd.to_numeric(
        temp[column],
        errors="coerce"
    ).dropna()

    if values.empty:
        return default

    return values.iloc[-1]


def safe_value(value, default=0):
    if pd.isna(value):
        return default

    return value


def format_number(value):
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.1f}"
    except Exception:
        return str(value)


def format_pct(value):
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "N/A"


# ============================================================
# COMPANY YEARS
# ============================================================

def count_years(company_id, cashflow, profitloss, balancesheet):
    """
    Count usable financial years.

    A company is considered valid if at least one of the
    financial datasets has 3 or more years.
    """

    counts = []

    for df in [cashflow, profitloss, balancesheet]:

        temp = company_data(df, company_id)

        if not temp.empty and "sort_year" in temp.columns:
            years = temp["sort_year"].dropna().unique()
            counts.append(len(years))

    if not counts:
        return 0

    return max(counts)


# ============================================================
# KPI CALCULATION
# ============================================================

def calculate_kpis(
    company_id,
    cashflow,
    profitloss,
    balancesheet,
    ratios,
    intelligence,
):
    cf = company_data(cashflow, company_id)
    pl = company_data(profitloss, company_id)
    bs = company_data(balancesheet, company_id)
    fr = company_data(ratios, company_id)

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    revenue = np.nan

    if not pl.empty and "sales" in pl.columns:
        revenue = latest_value(pl, "sales")

    # --------------------------------------------------------
    # Net Profit
    # --------------------------------------------------------

    net_profit = np.nan

    if not pl.empty and "net_profit" in pl.columns:
        net_profit = latest_value(pl, "net_profit")

    # --------------------------------------------------------
    # EPS
    # --------------------------------------------------------

    eps = np.nan

    if not pl.empty and "eps" in pl.columns:
        eps = latest_value(pl, "eps")

    # --------------------------------------------------------
    # ROE
    # --------------------------------------------------------

    roe = np.nan

    if not fr.empty and "return_on_equity_pct" in fr.columns:
        roe = latest_value(fr, "return_on_equity_pct")

    # --------------------------------------------------------
    # ROCE
    # --------------------------------------------------------

    roce = np.nan

    # companies table does not need to be used here;
    # derive from available ratio if present
    if "roce_pct" in fr.columns:
        roce = latest_value(fr, "roce_pct")

    # --------------------------------------------------------
    # Debt / Equity
    # --------------------------------------------------------

    debt_equity = np.nan

    if not fr.empty and "debt_to_equity" in fr.columns:
        debt_equity = latest_value(fr, "debt_to_equity")

    # --------------------------------------------------------
    # CFO
    # --------------------------------------------------------

    cfo = np.nan

    if not cf.empty and "operating_activity" in cf.columns:
        cfo = latest_value(cf, "operating_activity")

    # --------------------------------------------------------
    # FCF
    # --------------------------------------------------------

    fcf = np.nan

    if not fr.empty and "free_cash_flow_cr" in fr.columns:
        fcf = latest_value(fr, "free_cash_flow_cr")

    if pd.isna(fcf) and not cf.empty:
        if (
            "operating_activity" in cf.columns
            and "investing_activity" in cf.columns
        ):
            temp_cfo = pd.to_numeric(
                cf["operating_activity"],
                errors="coerce"
            )

            temp_cfi = pd.to_numeric(
                cf["investing_activity"],
                errors="coerce"
            )

            fcf_series = temp_cfo + temp_cfi

            fcf_values = fcf_series.dropna()

            if not fcf_values.empty:
                fcf = fcf_values.iloc[-1]

    # --------------------------------------------------------
    # Intelligence values
    # --------------------------------------------------------

    intelligence_row = pd.DataFrame()

    if not intelligence.empty and "company_id" in intelligence.columns:

        intelligence_row = intelligence[
            intelligence["company_id"].astype(str).str.strip()
            == str(company_id).strip()
        ]

    capital_allocation = "Insufficient Data"
    cfo_quality = "N/A"
    capex_label = "N/A"

    if not intelligence_row.empty:

        row = intelligence_row.iloc[-1]

        if "capital_allocation_label" in row.index:
            capital_allocation = safe_value(
                row["capital_allocation_label"],
                "Insufficient Data"
            )

        if "cfo_quality_label" in row.index:
            cfo_quality = safe_value(
                row["cfo_quality_label"],
                "N/A"
            )

        if "capex_label" in row.index:
            capex_label = safe_value(
                row["capex_label"],
                "N/A"
            )

    return {
        "revenue": revenue,
        "net_profit": net_profit,
        "eps": eps,
        "roe": roe,
        "roce": roce,
        "debt_equity": debt_equity,
        "cfo": cfo,
        "fcf": fcf,
        "cfo_quality": cfo_quality,
        "capex_label": capex_label,
        "capital_allocation": capital_allocation,
    }


# ============================================================
# CHART 1 — REVENUE / NET PROFIT
# ============================================================

def create_revenue_profit_chart(company_id, profitloss):

    df = company_data(profitloss, company_id)

    if df.empty or "sales" not in df.columns:
        return None

    if "net_profit" not in df.columns:
        return None

    df = df.dropna(subset=["sort_year"])

    if df.empty:
        return None

    df = df.tail(10)

    years = df["sort_year"].astype(int).astype(str)

    revenue = pd.to_numeric(
        df["sales"],
        errors="coerce"
    )

    profit = pd.to_numeric(
        df["net_profit"],
        errors="coerce"
    )

    fig, ax = plt.subplots(figsize=(6.7, 2.6))

    x = np.arange(len(years))
    width = 0.36

    ax.bar(
        x - width / 2,
        revenue,
        width,
        label="Revenue"
    )

    ax.bar(
        x + width / 2,
        profit,
        width,
        label="Net Profit"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(years, rotation=45, fontsize=6)

    ax.set_title(
        "10-Year Revenue and Net Profit",
        fontsize=9
    )

    ax.legend(fontsize=7)

    ax.grid(
        axis="y",
        alpha=0.2
    )

    fig.tight_layout()

    path = CHART_DIR / f"{company_id}_revenue_profit.png"

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


# ============================================================
# CHART 2 — ROE / ROCE
# ============================================================

def create_roe_roce_chart(company_id, ratios):

    df = company_data(ratios, company_id)

    if df.empty:
        return None

    if "return_on_equity_pct" not in df.columns:
        return None

    df = df.dropna(subset=["sort_year"])

    if df.empty:
        return None

    df = df.tail(10)

    years = df["sort_year"].astype(int).astype(str)

    roe = pd.to_numeric(
        df["return_on_equity_pct"],
        errors="coerce"
    )

    roce = None

    if "roce_pct" in df.columns:
        roce = pd.to_numeric(
            df["roce_pct"],
            errors="coerce"
        )

    fig, ax = plt.subplots(figsize=(6.7, 2.5))

    ax.plot(
        years,
        roe,
        marker="o",
        linewidth=1.5,
        label="ROE"
    )

    if roce is not None:
        ax.plot(
            years,
            roce,
            marker="o",
            linewidth=1.5,
            label="ROCE"
        )

    ax.set_title(
        "ROE and ROCE Trend",
        fontsize=9
    )

    ax.set_ylabel(
        "%",
        fontsize=7
    )

    ax.tick_params(
        axis="x",
        labelrotation=45,
        labelsize=6
    )

    ax.legend(fontsize=7)

    ax.grid(
        alpha=0.2
    )

    fig.tight_layout()

    path = CHART_DIR / f"{company_id}_roe_roce.png"

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


# ============================================================
# CHART 3 — BALANCE SHEET
# ============================================================

def create_balance_chart(company_id, balancesheet):

    df = company_data(
        balancesheet,
        company_id
    )

    if df.empty:
        return None

    required = [
        "reserves",
        "borrowings",
        "other_liabilities",
    ]

    if not all(
        col in df.columns
        for col in required
    ):
        return None

    df = df.dropna(subset=["sort_year"])

    if df.empty:
        return None

    df = df.tail(10)

    years = df["sort_year"].astype(int).astype(str)

    reserves = pd.to_numeric(
        df["reserves"],
        errors="coerce"
    ).fillna(0)

    borrowings = pd.to_numeric(
        df["borrowings"],
        errors="coerce"
    ).fillna(0)

    other = pd.to_numeric(
        df["other_liabilities"],
        errors="coerce"
    ).fillna(0)

    fig, ax = plt.subplots(figsize=(6.7, 2.6))

    ax.bar(
        years,
        reserves,
        label="Equity / Reserves"
    )

    ax.bar(
        years,
        borrowings,
        bottom=reserves,
        label="Borrowings"
    )

    ax.bar(
        years,
        other,
        bottom=reserves + borrowings,
        label="Other Liabilities"
    )

    ax.set_title(
        "Balance Sheet Composition",
        fontsize=9
    )

    ax.tick_params(
        axis="x",
        labelrotation=45,
        labelsize=6
    )

    ax.legend(fontsize=6)

    ax.grid(
        axis="y",
        alpha=0.2
    )

    fig.tight_layout()

    path = CHART_DIR / f"{company_id}_balance.png"

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


# ============================================================
# CHART 4 — CASH FLOW
# ============================================================

def create_cashflow_chart(company_id, cashflow):

    df = company_data(
        cashflow,
        company_id
    )

    if df.empty:
        return None

    required = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    if not all(
        col in df.columns
        for col in required
    ):
        return None

    df = df.dropna(subset=["sort_year"])

    if df.empty:
        return None

    row = df.iloc[-1]

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net Cash Flow",
    ]

    values = [
        pd.to_numeric(
            row["operating_activity"],
            errors="coerce"
        ),
        pd.to_numeric(
            row["investing_activity"],
            errors="coerce"
        ),
        pd.to_numeric(
            row["financing_activity"],
            errors="coerce"
        ),
        pd.to_numeric(
            row["net_cash_flow"],
            errors="coerce"
        ),
    ]

    values = [
        0 if pd.isna(v) else v
        for v in values
    ]

    fig, ax = plt.subplots(figsize=(6.7, 2.6))

    x = np.arange(len(labels))

    ax.bar(
        x,
        values
    )

    ax.axhline(
        0,
        linewidth=0.8
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        labels,
        fontsize=7
    )

    ax.set_title(
        "Latest Year Cash Flow",
        fontsize=9
    )

    ax.grid(
        axis="y",
        alpha=0.2
    )

    fig.tight_layout()

    path = CHART_DIR / f"{company_id}_cashflow.png"

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


# ============================================================
# PROS / CONS
# ============================================================

def get_pros_cons(
    company_id,
    proscons
):

    if proscons.empty:
        return [], []

    if "company_id" not in proscons.columns:
        return [], []

    temp = proscons[
        proscons["company_id"].astype(str).str.strip()
        == str(company_id).strip()
    ].copy()

    if temp.empty:
        return [], []

    if "confidence_pct" in temp.columns:
        temp["confidence_pct"] = pd.to_numeric(
            temp["confidence_pct"],
            errors="coerce"
        )

        temp = temp[
            temp["confidence_pct"] >= 60
        ]

    pros = temp[
        temp["type"].astype(str).str.lower()
        == "pro"
    ]

    cons = temp[
        temp["type"].astype(str).str.lower()
        == "con"
    ]

    return (
        pros["text"].astype(str).tolist()[:6],
        cons["text"].astype(str).tolist()[:6],
    )


# ============================================================
# PDF HEADER
# ============================================================

def draw_header(canvas, doc, company_id, company_name):

    canvas.saveState()

    canvas.setFillColor(NAVY)

    canvas.rect(
        0,
        PAGE_HEIGHT - 30 * mm,
        PAGE_WIDTH,
        30 * mm,
        fill=1,
        stroke=0
    )

    canvas.setFillColor(WHITE)

    canvas.setFont(
        "Helvetica-Bold",
        18
    )

    canvas.drawString(
        15 * mm,
        PAGE_HEIGHT - 14 * mm,
        str(company_name)[:70]
    )

    canvas.setFont(
        "Helvetica",
        9
    )

    canvas.drawString(
        15 * mm,
        PAGE_HEIGHT - 22 * mm,
        f"Ticker: {company_id}"
    )

    canvas.restoreState()


# ============================================================
# KPI TILES
# ============================================================

def create_kpi_tiles(kpis):

    data = [
        [
            Paragraph(
                f"<b>Revenue</b><br/>{format_number(kpis['revenue'])}",
                CENTER_STYLE,
            ),
            Paragraph(
                f"<b>Net Profit</b><br/>{format_number(kpis['net_profit'])}",
                CENTER_STYLE,
            ),
            Paragraph(
                f"<b>EPS</b><br/>{format_number(kpis['eps'])}",
                CENTER_STYLE,
            ),
        ],
        [
            Paragraph(
                f"<b>ROE</b><br/>{format_pct(kpis['roe'])}",
                CENTER_STYLE,
            ),
            Paragraph(
                f"<b>Debt / Equity</b><br/>{format_number(kpis['debt_equity'])}",
                CENTER_STYLE,
            ),
            Paragraph(
                f"<b>FCF</b><br/>{format_number(kpis['fcf'])}",
                CENTER_STYLE,
            ),
        ],
    ]

    table = Table(
        data,
        colWidths=[
            58 * mm,
            58 * mm,
            58 * mm,
        ],
        rowHeights=[
            18 * mm,
            18 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_GREY,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.white,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
            ]
        )
    )

    return table


# ============================================================
# PRO / CON TABLE
# ============================================================

def create_pro_con_table(pros, cons):

    pro_rows = [
        [
            Paragraph(
                "<b>PROS</b>",
                ParagraphStyle(
                    "ProHeading",
                    parent=NORMAL_STYLE,
                    textColor=GREEN,
                    fontSize=9,
                ),
            )
        ]
    ]

    for text in pros:
        pro_rows.append(
            [
                Paragraph(
                    "• " + text,
                    PRO_STYLE
                )
            ]
        )

    if len(pro_rows) == 1:
        pro_rows.append(
            [
                Paragraph(
                    "• No significant positive signal available.",
                    PRO_STYLE,
                )
            ]
        )

    con_rows = [
        [
            Paragraph(
                "<b>CONS</b>",
                ParagraphStyle(
                    "ConHeading",
                    parent=NORMAL_STYLE,
                    textColor=RED,
                    fontSize=9,
                ),
            )
        ]
    ]

    for text in cons:
        con_rows.append(
            [
                Paragraph(
                    "• " + text,
                    CON_STYLE
                )
            ]
        )

    if len(con_rows) == 1:
        con_rows.append(
            [
                Paragraph(
                    "• No significant negative signal available.",
                    CON_STYLE,
                )
            ]
        )

    max_rows = max(
        len(pro_rows),
        len(con_rows)
    )

    while len(pro_rows) < max_rows:
        pro_rows.append([""])

    while len(con_rows) < max_rows:
        con_rows.append([""])

    combined = []

    for i in range(max_rows):

        left = pro_rows[i][0]

        right = con_rows[i][0]

        combined.append(
            [
                left,
                right,
            ]
        )

    table = Table(
        combined,
        colWidths=[
            87 * mm,
            87 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.lightgrey,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return table


# ============================================================
# CAPITAL ALLOCATION BADGE
# ============================================================

def create_capital_badge(label):

    table = Table(
        [
            [
                Paragraph(
                    f"<b>Capital Allocation: {label}</b>",
                    CENTER_STYLE,
                )
            ]
        ],
        colWidths=[175 * mm],
        rowHeights=[12 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, -1),
                    WHITE,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    NAVY,
                ),
            ]
        )
    )

    return table


# ============================================================
# GENERATE ONE TEARSHEET
# ============================================================

def generate_tearsheet(
    company_id,
    company_name,
    cashflow,
    profitloss,
    balancesheet,
    ratios,
    proscons,
    intelligence,
):

    years = count_years(
        company_id,
        cashflow,
        profitloss,
        balancesheet,
    )

    if years < 3:
        return False, "Fewer than 3 years of data"

    output_file = (
        OUTPUT_DIR
        / f"{company_id}_tearsheet.pdf"
    )

    kpis = calculate_kpis(
        company_id,
        cashflow,
        profitloss,
        balancesheet,
        ratios,
        intelligence,
    )

    revenue_chart = create_revenue_profit_chart(
        company_id,
        profitloss,
    )

    roe_chart = create_roe_roce_chart(
        company_id,
        ratios,
    )

    balance_chart = create_balance_chart(
        company_id,
        balancesheet,
    )

    cashflow_chart = create_cashflow_chart(
        company_id,
        cashflow,
    )

    pros, cons = get_pros_cons(
        company_id,
        proscons,
    )

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=35 * mm,
        bottomMargin=12 * mm,
        title=f"{company_id} Tearsheet",
        author="Sprint 5",
    )

    story = []

    # ========================================================
    # PAGE 1
    # ========================================================

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        create_kpi_tiles(kpis)
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            "Financial Performance",
            SECTION_STYLE,
        )
    )

    if revenue_chart:

        story.append(
            Image(
                str(revenue_chart),
                width=175 * mm,
                height=68 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Revenue / Net Profit chart unavailable.",
                NORMAL_STYLE,
            )
        )

    story.append(
        Spacer(1, 3 * mm)
    )

    if roe_chart:

        story.append(
            Image(
                str(roe_chart),
                width=175 * mm,
                height=65 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "ROE / ROCE chart unavailable.",
                NORMAL_STYLE,
            )
        )

    story.append(
        PageBreak()
    )

    # ========================================================
    # PAGE 2
    # ========================================================

    story.append(
        Paragraph(
            "Balance Sheet Composition",
            SECTION_STYLE,
        )
    )

    if balance_chart:

        story.append(
            Image(
                str(balance_chart),
                width=175 * mm,
                height=66 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Balance Sheet chart unavailable.",
                NORMAL_STYLE,
            )
        )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Paragraph(
            "Cash Flow",
            SECTION_STYLE,
        )
    )

    if cashflow_chart:

        story.append(
            Image(
                str(cashflow_chart),
                width=175 * mm,
                height=60 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Cash Flow chart unavailable.",
                NORMAL_STYLE,
            )
        )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        create_capital_badge(
            kpis["capital_allocation"]
        )
    )

    story.append(
        Spacer(1, 4 * mm)
    )

    story.append(
        create_pro_con_table(
            pros,
            cons,
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(
        story,
        onFirstPage=lambda canvas, doc: draw_header(
            canvas,
            doc,
            company_id,
            company_name,
        ),
        onLaterPages=lambda canvas, doc: draw_header(
            canvas,
            doc,
            company_id,
            company_name,
        ),
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not output_file.exists():
        return False, "PDF was not created"

    size = output_file.stat().st_size

    if size < 30_000:
        return True, f"PDF created but below 30 KB ({size / 1024:.1f} KB)"

    return True, f"{size / 1024:.1f} KB"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("==============================================")
    print("      Sprint 5 — Tearsheet Generator")
    print("==============================================")
    print()

    print(f"Database : {DB_PATH}")
    print(f"Output   : {OUTPUT_DIR}")

    (
        companies,
        cashflow,
        profitloss,
        balancesheet,
        ratios,
        proscons,
        intelligence,
    ) = load_database()

    # ========================================================
    # CRITICAL FIX
    # ========================================================
    #
    # Use ONLY the companies table for the official universe.
    #
    # companies table = 92
    # cashflow table = 100
    #
    # Therefore we NEVER use cashflow.company_id to determine
    # which companies to generate.
    # ========================================================

    company_ids = (
        companies["company_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    print()
    print("----------------------------------------------")
    print("Official Sprint 5 Company Universe")
    print("----------------------------------------------")
    print(
        f"Companies to generate : {len(company_ids)}"
    )

    if len(company_ids) != 92:

        print()
        print(
            "WARNING: Expected 92 official companies "
            f"but found {len(company_ids)}."
        )

    # ========================================================
    # COMPANY NAME LOOKUP
    # ========================================================

    name_map = {}

    for _, row in companies.iterrows():

        ticker = str(
            row["company_id"]
        ).strip()

        name = str(
            row["company_name"]
        ).strip()

        name_map[ticker] = name

    # ========================================================
    # GENERATE
    # ========================================================

    generated = 0
    failed = 0
    skipped = 0

    skipped_rows = []

    print()

    for index, company_id in enumerate(
        company_ids,
        start=1
    ):

        company_name = name_map.get(
            company_id,
            company_id
        )

        try:

            success, message = generate_tearsheet(
                company_id,
                company_name,
                cashflow,
                profitloss,
                balancesheet,
                ratios,
                proscons,
                intelligence,
            )

            if success:

                generated += 1

                print(
                    f"[{index:3d}/{len(company_ids)}] "
                    f"{company_id:<16} "
                    f"{message}  "
                    f"{company_id}_tearsheet.pdf"
                )

                if "below 30 KB" in message:

                    print(
                        f"WARNING: {company_id} "
                        f"PDF is below 30 KB."
                    )

            else:

                skipped += 1

                skipped_rows.append(
                    {
                        "company_id": company_id,
                        "reason": message,
                    }
                )

                print(
                    f"[{index:3d}/{len(company_ids)}] "
                    f"{company_id:<16} "
                    f"SKIPPED: {message}"
                )

        except Exception as exc:

            failed += 1

            skipped_rows.append(
                {
                    "company_id": company_id,
                    "reason": str(exc),
                }
            )

            print(
                f"[{index:3d}/{len(company_ids)}] "
                f"{company_id:<16} "
                f"FAILED: {exc}"
            )

    # ========================================================
    # SKIPPED FILE
    # ========================================================

    skipped_file = (
        ROOT_DIR
        / "output"
        / "skipped_tearsheets.csv"
    )

    skipped_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    pd.DataFrame(
        skipped_rows,
        columns=[
            "company_id",
            "reason",
        ],
    ).to_csv(
        skipped_file,
        index=False,
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("==============================================")
    print("Tearsheet Generation Completed")
    print("==============================================")

    print(
        f"Official companies : {len(company_ids)}"
    )

    print(
        f"Generated           : {generated}"
    )

    print(
        f"Skipped             : {skipped}"
    )

    print(
        f"Failed              : {failed}"
    )

    print(
        f"Output              : {OUTPUT_DIR}"
    )

    print(
        f"Skipped log         : {skipped_file}"
    )

    print()

    if len(company_ids) == 92:
        print(
            "SUCCESS: Official Sprint 5 universe "
            "contains exactly 92 companies."
        )
    else:
        print(
            "WARNING: Official company count is not 92."
        )


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":
    main()