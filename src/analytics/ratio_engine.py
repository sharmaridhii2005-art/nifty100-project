"""
Ratio Engine
Sprint 2 - Day 12
Reads financial data from SQLite and calculates KPIs.
"""

import sqlite3
import os
import logging

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    debt_to_equity,
    interest_coverage_ratio,
    asset_turnover,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    capex_intensity,
)

# ----------------------------------------------------
# Connect to SQLite Database
# ----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "nifty100.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Connected to:", DB_PATH)
# ----------------------------------------------------
# Logging Configuration
# ----------------------------------------------------

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(OUTPUT_DIR, "ratio_edge_cases.log"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# ----------------------------------------------------
# Read financial data
# ----------------------------------------------------

query = """
SELECT
    p.company_id,
    p.year,

    p.sales,
    p.operating_profit,
    p.opm_percentage,
    p.other_income,
    p.interest,
    p.net_profit,
    p.eps,
    p.dividend_payout,

    b.equity_capital,
    b.reserves,
    b.borrowings,
    b.investments,
    b.total_assets,

    c.operating_activity,
    c.investing_activity,
    c.financing_activity

FROM profitandloss p

JOIN balancesheet b
ON p.company_id = b.company_id
AND p.year = b.year

JOIN cashflow c
ON p.company_id = c.company_id
AND p.year = c.year
"""

cursor.execute(query)

rows = cursor.fetchall()

print("Rows fetched:", len(rows))

# ----------------------------------------------------
# Calculate KPIs
# ----------------------------------------------------

for row in rows:

    (
        company_id,
        year,
        sales,
        operating_profit,
        opm_percentage,
        other_income,
        interest,
        net_profit,
        eps,
        dividend_payout,
        equity_capital,
        reserves,
        borrowings,
        investments,
        total_assets,
        operating_activity,
        investing_activity,
        financing_activity,
    ) = row

    # ---------------- Logging ----------------

    if sales is None:
        logging.info(f"{company_id} {year}: Sales is NULL")

    if operating_profit is None:
        logging.info(f"{company_id} {year}: Operating Profit is NULL")

    if equity_capital is None:
        logging.info(f"{company_id} {year}: Equity Capital is NULL")

    if total_assets is None:
        logging.info(f"{company_id} {year}: Total Assets is NULL")

    # ---------------- Profitability ----------------

    npm = net_profit_margin(net_profit, sales)

    opm = operating_profit_margin(
        operating_profit,
        sales
    )

    roe = return_on_equity(
        net_profit,
        equity_capital,
        reserves
    )

    # ---------------- Leverage ----------------

    de = debt_to_equity(
        borrowings,
        equity_capital,
        reserves
    )

    icr = interest_coverage_ratio(
        operating_profit,
        other_income,
        interest
    )

    turnover = asset_turnover(
        sales,
        total_assets
    )

    # ---------------- Cash Flow ----------------

    if operating_activity is None:
        operating_activity = 0

    if investing_activity is None:
        investing_activity = 0

    fcf = free_cash_flow(
        operating_activity,
        investing_activity
    )

    capex = capex_intensity(
        investing_activity,
        sales
    )

    cursor.execute("""
INSERT INTO financial_ratios (
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
    dividend_payout_ratio_pct,
    total_debt_cr,
    cash_from_operations_cr
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
        company_id,
        year,
        npm,
        opm,
        roe,
        de,
        icr,
        turnover,
        fcf,
        capex,
        eps,
        dividend_payout,
        borrowings,
        operating_activity
    ))

print("====================================")

print("====================================")
print("Ratio Engine Completed Successfully")
print("Rows Processed:", len(rows))
print("====================================")
conn.commit()
conn.close()




