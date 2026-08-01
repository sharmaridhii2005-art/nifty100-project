import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# -------------------------------
# Database Configuration
# -------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "db" / "nifty100.db"


# -------------------------------
# Database Connection
# -------------------------------

def get_connection():
    """Create SQLite connection."""
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def run_query(query, params=()):
    """Execute SQL query and return DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# ============================================================
# Companies
# ============================================================

@st.cache_data(ttl=600)
def get_companies():
    """Return all companies."""
    return run_query("""
        SELECT *
        FROM companies
        ORDER BY company_name
    """)


@st.cache_data(ttl=600)
def get_company(company_id):
    """Return one company."""
    return run_query("""
        SELECT *
        FROM companies
        WHERE id = ?
    """, (company_id,))


# ============================================================
# Financial Ratios
# ============================================================

@st.cache_data(ttl=600)
def get_ratios(company_id, year=None):
    """Return financial ratios."""

    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """

    params = [company_id]

    if year is not None:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year"

    return run_query(query, tuple(params))


# ============================================================
# Profit & Loss
# ============================================================

@st.cache_data(ttl=600)
def get_pl(company_id):
    return run_query("""
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
    """, (company_id,))


# ============================================================
# Balance Sheet
# ============================================================

@st.cache_data(ttl=600)
def get_bs(company_id):
    return run_query("""
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
    """, (company_id,))


# ============================================================
# Cash Flow
# ============================================================

@st.cache_data(ttl=600)
def get_cf(company_id):
    return run_query("""
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
    """, (company_id,))


# ============================================================
# Market Cap / Valuation
# ============================================================

@st.cache_data(ttl=600)
def get_valuation(company_id):
    return run_query("""
        SELECT *
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year
    """, (company_id,))


# ============================================================
# Sectors
# ============================================================

@st.cache_data(ttl=600)
def get_sectors():
    return run_query("""
        SELECT *
        FROM sectors
        ORDER BY broad_sector
    """)


# ============================================================
# Peer Groups
# ============================================================

@st.cache_data(ttl=600)
def get_peer_groups():
    return run_query("""
        SELECT *
        FROM peer_groups
        ORDER BY peer_group_name
    """)


@st.cache_data(ttl=600)
def get_peers(group_name):
    return run_query("""
        SELECT *
        FROM peer_groups
        WHERE peer_group_name = ?
    """, (group_name,))


# ============================================================
# Pros & Cons
# ============================================================

@st.cache_data(ttl=600)
def get_pros_cons(company_id):
    return run_query("""
        SELECT *
        FROM prosandcons
        WHERE company_id = ?
    """, (company_id,))


# ============================================================
# Stock Prices
# ============================================================

@st.cache_data(ttl=600)
def get_stock_prices():
    """
    Returns stock_prices table.

    NOTE:
    Your stock_prices table currently has incorrect column names
    because the first data row became the header during import.
    This function simply returns the table as-is.
    """
    return run_query("""
        SELECT *
        FROM stock_prices
    """)


# ============================================================
# Dashboard Summary
# ============================================================

@st.cache_data(ttl=600)
def get_dashboard_data():
    """
    Home page data.
    Joins companies + sectors + latest ratios.
    """

    query = """
    SELECT
        c.id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        r.year,
        r.return_on_equity_pct,
        r.debt_to_equity,
        r.net_profit_margin_pct,
        r.operating_profit_margin_pct,
        r.free_cash_flow_cr
    FROM companies c

    LEFT JOIN sectors s
        ON c.id = s.company_id

    LEFT JOIN financial_ratios r
        ON c.id = r.company_id
    """

    return run_query(query)