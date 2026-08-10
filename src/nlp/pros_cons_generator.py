import os
import sqlite3
import pandas as pd

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
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


# -----------------------------
# Database
# -----------------------------
conn = sqlite3.connect(DB_PATH)

ratios = pd.read_sql(
    """
    SELECT *
    FROM financial_ratios
    """,
    conn
)

companies = pd.read_sql(
    """
    SELECT *
    FROM companies
    """,
    conn
)

sectors = pd.read_sql(
    """
    SELECT *
    FROM sectors
    """,
    conn
)

conn.close()


# -----------------------------
# Merge latest year
# -----------------------------
ratios["year"] = pd.to_numeric(
    ratios["year"],
    errors="coerce"
)

latest = (
    ratios
    .sort_values("year")
    .groupby("company_id")
    .tail(1)
)

latest = latest.merge(
    companies,
    left_on="company_id",
    right_on="id",
    how="left"
)

latest = latest.merge(
    sectors,
    on="company_id",
    how="left"
)


results = []
numeric_cols = [
    "return_on_equity_pct",
    "free_cash_flow_cr",
    "debt_to_equity",
    "operating_profit_margin_pct",
    "interest_coverage",
    "dividend_payout_ratio_pct",
    "asset_turnover",
    "net_profit_margin_pct",
    "earnings_per_share",
    "book_value_per_share",
    "cash_from_operations_cr",
    "total_debt_cr"
]

for col in numeric_cols:
    if col in latest.columns:
        latest[col] = pd.to_numeric(latest[col], errors="coerce").fillna(0)


# -----------------------------
# Helper
# -----------------------------
def add_result(
    company,
    result_type,
    rule_id,
    text,
    confidence
):

    results.append(
        {
            "company_id": company,
            "type": result_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": confidence
        }
    )


print("--------------------------------")
print("Pros / Cons Generator Started")
print("--------------------------------")
print()

print("Companies :", latest["company_id"].nunique())
print()
# ----------------------------------------------------
# PRO RULES
# ----------------------------------------------------

for _, row in latest.iterrows():

    company = row["company_id"]

    # Rule P1
    if row.get("return_on_equity_pct", 0) > 20:
        add_result(
            company,
            "pro",
            "P1",
            "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.",
            95
        )

    # Rule P2
    if row.get("free_cash_flow_cr", 0) > 0:
        add_result(
            company,
            "pro",
            "P2",
            "Strong free cash flow generation signals healthy business fundamentals.",
            90
        )

    # Rule P3
    if row.get("debt_to_equity", 999) == 0:
        add_result(
            company,
            "pro",
            "P3",
            "Debt-free balance sheet provides financial flexibility and eliminates interest burden.",
            98
        )

    # Rule P4
    if row.get("operating_profit_margin_pct", 0) > 25:
        add_result(
            company,
            "pro",
            "P4",
            "Operating profit margin above 25% indicates strong pricing power and cost discipline.",
            90
        )

    # Rule P5
    if row.get("interest_coverage", 0) > 10:
        add_result(
            company,
            "pro",
            "P5",
            "Very high interest coverage reflects negligible financial stress.",
            88
        )

    # Rule P6
    if row.get("dividend_payout_ratio_pct", 0) > 30:
        add_result(
            company,
            "pro",
            "P6",
            "Healthy dividend payout reflects shareholder-friendly capital allocation.",
            82
        )

    # Rule P7
    if row.get("asset_turnover", 0) > 1:
        add_result(
            company,
            "pro",
            "P7",
            "Efficient utilization of assets supports strong operating performance.",
            80
        )

    # Rule P8
    if row.get("net_profit_margin_pct", 0) > 15:
        add_result(
            company,
            "pro",
            "P8",
            "Healthy profit margins demonstrate strong profitability.",
            84
        )

    # Rule P9
    if row.get("earnings_per_share", 0) > 0:
        add_result(
            company,
            "pro",
            "P9",
            "Positive earnings per share indicate profitable operations.",
            78
        )

    # Rule P10
    if row.get("book_value_per_share", 0) > 0:
        add_result(
            company,
            "pro",
            "P10",
            "Positive book value per share reflects a solid equity base.",
            75
        )

    # Rule P11
    if row.get("cash_from_operations_cr", 0) > 0:
        add_result(
            company,
            "pro",
            "P11",
            "Positive cash flow from operations supports business sustainability.",
            90
        )

    # Rule P12
    if (
        row.get("free_cash_flow_cr", 0) > 0
        and row.get("cash_from_operations_cr", 0) > 0
    ):
        add_result(
            company,
            "pro",
            "P12",
            "Strong operating cash flow backed by positive free cash flow reflects high-quality earnings.",
            95
        )
        # ----------------------------------------------------
# CON RULES
# ----------------------------------------------------

for _, row in latest.iterrows():

    company = row["company_id"]

    # Rule C1
    if (
        row.get("debt_to_equity", 0) > 2
        and row.get("broad_sector", "") != "Financials"
    ):
        add_result(
            company,
            "con",
            "C1",
            f"Debt-to-equity ratio of {row['debt_to_equity']:.2f} is elevated for a non-financial company.",
            95
        )

    # Rule C2
    if row.get("free_cash_flow_cr", 0) < 0:
        add_result(
            company,
            "con",
            "C2",
            "Negative free cash flow raises concern about cash generation.",
            85
        )

    # Rule C3
    if row.get("operating_profit_margin_pct", 0) < 10:
        add_result(
            company,
            "con",
            "C3",
            "Operating margin is relatively low.",
            75
        )

    # Rule C4
    if row.get("net_profit_margin_pct", 0) < 0:
        add_result(
            company,
            "con",
            "C4",
            "Company reported a net loss in the latest year.",
            95
        )

    # Rule C5
    if row.get("interest_coverage", 999) < 1.5:
        add_result(
            company,
            "con",
            "C5",
            "Interest coverage ratio below 1.5x indicates financial stress.",
            90
        )

    # Rule C6
    if row.get("dividend_payout_ratio_pct", 0) > 100:
        add_result(
            company,
            "con",
            "C6",
            "Dividend payout ratio above 100% appears unsustainable.",
            92
        )

    # Rule C7
    if row.get("asset_turnover", 99) < 0.3:
        add_result(
            company,
            "con",
            "C7",
            "Low asset turnover indicates inefficient asset utilization.",
            72
        )

    # Rule C8
    if row.get("return_on_equity_pct", 100) < 10:
        add_result(
            company,
            "con",
            "C8",
            "Return on equity below 10% suggests weak shareholder returns.",
            82
        )

    # Rule C9
    if row.get("earnings_per_share", 0) < 0:
        add_result(
            company,
            "con",
            "C9",
            "Negative earnings per share reflects poor profitability.",
            90
        )

    # Rule C10
    if row.get("cash_from_operations_cr", 0) < 0:
        add_result(
            company,
            "con",
            "C10",
            "Negative operating cash flow indicates weak cash generation.",
            88
        )

    # Rule C11
    if row.get("total_debt_cr", 0) > 50000:
        add_result(
            company,
            "con",
            "C11",
            "High debt levels should be monitored carefully.",
            70
        )

    # Rule C12
    # Rule C12
book_value = row.get("book_value_per_share")

if pd.notna(book_value) and book_value <= 0:
    add_result(
        company,
        "con",
        "C12",
        "Book value per share is weak.",
        65
    )

# ----------------------------------------------------
# Build DataFrame
# ----------------------------------------------------

result = pd.DataFrame(results)

result = result[result["confidence_pct"] >= 60]

# ----------------------------------------------------
# Ensure every company has at least one pro and one con
# ----------------------------------------------------

companies_list = latest["company_id"].unique()

for company in companies_list:

    company_rows = result[result["company_id"] == company]

    if "pro" not in company_rows["type"].values:
        result.loc[len(result)] = [
            company,
            "pro",
            "DEFAULT_PRO",
            "Company maintains an established business presence.",
            60
        ]

    if "con" not in company_rows["type"].values:
        result.loc[len(result)] = [
            company,
            "con",
            "DEFAULT_CON",
            "Business performance should continue to be monitored.",
            60
        ]

# ----------------------------------------------------
# Save CSV
# ----------------------------------------------------

output_file = os.path.join(
    OUTPUT_DIR,
    "pros_cons_generated.csv"
)

result.to_csv(
    output_file,
    index=False
)

print("--------------------------------")
print("Pros / Cons Generation Completed")
print("--------------------------------")
print()

print("Companies :", result["company_id"].nunique())
print("Records   :", len(result))
print()
print("Created :", output_file)