import os
import re
import sqlite3
import pandas as pd

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

ANALYSIS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "analysis.xlsx"
)

DB_FILE = os.path.join(
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
# Regex
# -----------------------------
YEAR_PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*(-?[\d.]+)%",
    re.IGNORECASE
)

NUMBER_PATTERN = re.compile(
    r"(-?[\d.]+)%"
)


# -----------------------------
# Parse function
# -----------------------------
def parse_text(text):

    if pd.isna(text):
        return None

    text = str(text).strip()

    # 10 Years / 5 Years / 3 Years
    match = YEAR_PATTERN.search(text)

    if match:
        return (
            int(match.group(1)),
            float(match.group(2))
        )

    # TTM
    if text.upper().startswith("TTM"):

        m = NUMBER_PATTERN.search(text)

        if m:
            return (
                0,
                float(m.group(1))
            )

    # Last Year
    if text.lower().startswith("last year"):

        m = NUMBER_PATTERN.search(text)

        if m:
            return (
                1,
                float(m.group(1))
            )

    # 1 Year
    if text.lower().startswith("1 year"):

        m = NUMBER_PATTERN.search(text)

        if m:
            return (
                1,
                float(m.group(1))
            )

    return None


# -----------------------------
# Main
# -----------------------------
def parse_analysis():

    print("-" * 45)
    print("Reading analysis.xlsx")
    print("-" * 45)

    analysis = pd.read_excel(
        ANALYSIS_FILE,
        header=1
    )

    metric_columns = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe"
    ]

    parsed_rows = []
    failed_rows = []

    for _, row in analysis.iterrows():

        company = row["company_id"]

        for metric in metric_columns:

            result = parse_text(row[metric])

            if result:

                period, value = result

                parsed_rows.append(
                    {
                        "company_id": company,
                        "metric_type": metric,
                        "period_years": period,
                        "value_pct": value
                    }
                )

            else:

                failed_rows.append(
                    {
                        "company_id": company,
                        "metric_type": metric,
                        "original_text": row[metric]
                    }
                )

    parsed_df = pd.DataFrame(parsed_rows)

    failed_df = pd.DataFrame(failed_rows)

    parsed_path = os.path.join(
        OUTPUT_DIR,
        "analysis_parsed.csv"
    )

    failure_path = os.path.join(
        OUTPUT_DIR,
        "parse_failures.csv"
    )

    parsed_df.to_csv(
        parsed_path,
        index=False
    )

    failed_df.to_csv(
        failure_path,
        index=False
    )

    print()
    print("-" * 45)
    print("Parser Completed Successfully")
    print("-" * 45)
    print(f"Parsed Records : {len(parsed_df)}")
    print(f"Failed Records : {len(failed_df)}")
    print()
    print(f"Created : {parsed_path}")
    print(f"Created : {failure_path}")

    # -----------------------------
    # Optional cross validation
    # -----------------------------
    try:

        conn = sqlite3.connect(DB_FILE)

        ratios = pd.read_sql(
            "SELECT company_id FROM financial_ratios",
            conn
        )

        conn.close()

        matched = parsed_df[
            parsed_df["company_id"].isin(
                ratios["company_id"].unique()
            )
        ]

        print()
        print("-" * 45)
        print("Cross Validation")
        print("-" * 45)
        print(
            "Companies found in Ratio Engine :",
            matched["company_id"].nunique()
        )

    except Exception as e:

        print()
        print("Cross validation skipped")
        print(e)


if __name__ == "__main__":
    parse_analysis()