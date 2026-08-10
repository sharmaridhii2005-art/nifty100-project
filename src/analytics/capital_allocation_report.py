import os
import sqlite3
import pandas as pd


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

INPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "cashflow_intelligence.xlsx"
)

SUMMARY_FILE = os.path.join(
    OUTPUT_DIR,
    "capital_allocation_summary.csv"
)

CHANGES_FILE = os.path.join(
    OUTPUT_DIR,
    "pattern_changes.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# NORMALIZE COMPANY ID
# ============================================================

def normalize_company_id(value):

    if pd.isna(value):
        return ""

    return str(value).strip().upper()


# ============================================================
# NORMALIZE YEAR
# ============================================================

def normalize_year(value):

    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    formats = [
        "%b-%y",
        "%b %Y",
        "%B %Y",
        "%Y"
    ]

    for fmt in formats:

        try:
            return pd.to_datetime(
                value,
                format=fmt
            )

        except (ValueError, TypeError):
            pass

    # Last attempt
    return pd.to_datetime(
        value,
        errors="coerce"
    )


# ============================================================
# LOAD CASH FLOW INTELLIGENCE
# ============================================================

def load_intelligence():

    print("--------------------------------")
    print("Loading Cash Flow Intelligence")
    print("--------------------------------")

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"\nFile not found:\n{INPUT_FILE}\n\n"
            "Run cashflow_kpis.py first."
        )

    df = pd.read_excel(
        INPUT_FILE
    )

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

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "\nMissing columns:\n"
            + "\n".join(missing_columns)
        )

    df["company_id"] = (
        df["company_id"]
        .apply(normalize_company_id)
    )

    return df


# ============================================================
# VERIFY 92 COMPANIES
# ============================================================

def verify_companies(df):

    print()
    print("--------------------------------")
    print("Verifying Companies")
    print("--------------------------------")

    rows = len(df)

    unique_companies = (
        df["company_id"]
        .nunique()
    )

    duplicates = (
        df["company_id"]
        .duplicated()
        .sum()
    )

    print("Rows             :", rows)
    print("Unique companies :", unique_companies)
    print("Duplicates       :", duplicates)

    if rows != 92:

        raise ValueError(
            f"Expected 92 rows but found {rows}"
        )

    if unique_companies != 92:

        raise ValueError(
            f"Expected 92 companies but found "
            f"{unique_companies}"
        )

    if duplicates != 0:

        raise ValueError(
            f"Found {duplicates} duplicate companies"
        )

    print()
    print(
        "SUCCESS: 92 unique companies verified."
    )


# ============================================================
# CAPITAL ALLOCATION DISTRIBUTION
# ============================================================

def create_distribution(df):

    print()
    print("--------------------------------")
    print("Capital Allocation Distribution")
    print("--------------------------------")

    distribution = (
        df[
            "capital_allocation_label"
        ]
        .fillna("Insufficient Data")
        .value_counts()
        .rename_axis(
            "capital_allocation_label"
        )
        .reset_index(
            name="company_count"
        )
    )

    distribution["percentage"] = (
        distribution["company_count"]
        / len(df)
        * 100
    ).round(2)

    # Save distribution
    distribution.to_csv(
        SUMMARY_FILE,
        index=False
    )

    print(
        distribution.to_string(
            index=False
        )
    )

    print()
    print(
        "Created:",
        SUMMARY_FILE
    )

    return distribution


# ============================================================
# LOAD RAW CASH FLOW
# ============================================================

def load_cashflow():

    print()
    print("--------------------------------")
    print("Loading Raw Cash Flow")
    print("--------------------------------")

    conn = sqlite3.connect(
        DB_PATH
    )

    query = """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
    """

    cashflow = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    cashflow["company_id"] = (
        cashflow["company_id"]
        .apply(normalize_company_id)
    )

    # Convert financial values to numbers
    numeric_columns = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow"
    ]

    for column in numeric_columns:

        cashflow[column] = pd.to_numeric(
            cashflow[column],
            errors="coerce"
        )

    cashflow["sort_year"] = (
        cashflow["year"]
        .apply(normalize_year)
    )

    print(
        "Cash flow records:",
        len(cashflow)
    )

    print(
        "Companies in cash flow:",
        cashflow["company_id"].nunique()
    )

    return cashflow


# ============================================================
# CLASSIFY CAPITAL ALLOCATION PATTERN
# ============================================================

def classify_pattern(row):

    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    cff = row["financing_activity"]

    if (
        pd.isna(cfo)
        or pd.isna(cfi)
        or pd.isna(cff)
    ):
        return "Insufficient Data"

    # --------------------------------------------------------
    # Distress Signal
    # CFO negative + financing positive
    # --------------------------------------------------------

    if cfo < 0 and cff > 0:

        return "Distress Signal"

    # --------------------------------------------------------
    # Cash Distributor
    # Positive CFO + negative financing
    # --------------------------------------------------------

    if cfo > 0 and cff < 0:

        return "Cash Distributor"

    # --------------------------------------------------------
    # Reinvestor
    # Positive CFO + negative investing
    # --------------------------------------------------------

    if cfo > 0 and cfi < 0:

        return "Reinvestor"

    # --------------------------------------------------------
    # Deleveraging
    # Negative financing cash flow
    # --------------------------------------------------------

    if cff < 0:

        return "Deleveraging"

    # --------------------------------------------------------
    # Positive CFO but no investment
    # --------------------------------------------------------

    if cfo > 0:

        return "Reinvestor"

    return "Insufficient Data"


# ============================================================
# BUILD HISTORICAL PATTERNS
# ============================================================

def build_patterns(cashflow):

    print()
    print("--------------------------------")
    print("Building Historical Patterns")
    print("--------------------------------")

    cashflow = cashflow.copy()

    cashflow["pattern"] = (
        cashflow.apply(
            classify_pattern,
            axis=1
        )
    )

    return cashflow


# ============================================================
# FIND YEAR-OVER-YEAR CHANGES
# ============================================================

def find_pattern_changes(cashflow):

    print()
    print("--------------------------------")
    print("Finding Pattern Changes")
    print("--------------------------------")

    df = cashflow.copy()

    # Remove rows where year could not be interpreted
    df = df.dropna(
        subset=["sort_year"]
    )

    df = df.sort_values(
        [
            "company_id",
            "sort_year"
        ]
    )

    changes = []

    for company_id, group in df.groupby(
        "company_id",
        sort=False
    ):

        group = group.reset_index(
            drop=True
        )

        for i in range(
            1,
            len(group)
        ):

            previous = group.iloc[i - 1]
            current = group.iloc[i]

            previous_pattern = (
                previous["pattern"]
            )

            current_pattern = (
                current["pattern"]
            )

            if (
                previous_pattern
                != current_pattern
            ):

                changes.append({

                    "company_id":
                        company_id,

                    "previous_year":
                        previous["year"],

                    "previous_pattern":
                        previous_pattern,

                    "current_year":
                        current["year"],

                    "current_pattern":
                        current_pattern
                })

    changes_df = pd.DataFrame(
        changes
    )

    if changes_df.empty:

        changes_df = pd.DataFrame(
            columns=[
                "company_id",
                "previous_year",
                "previous_pattern",
                "current_year",
                "current_pattern"
            ]
        )

    changes_df.to_csv(
        CHANGES_FILE,
        index=False
    )

    print(
        "Pattern changes detected:",
        len(changes_df)
    )

    print(
        "Created:",
        CHANGES_FILE
    )

    return changes_df


# ============================================================
# MAIN
# ============================================================

def generate_report():

    print()
    print("========================================")
    print(" DAY 32 - CAPITAL ALLOCATION REPORT")
    print("========================================")
    print()

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    intelligence = (
        load_intelligence()
    )

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    verify_companies(
        intelligence
    )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    create_distribution(
        intelligence
    )

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    cashflow = load_cashflow()

    # --------------------------------------------------------
    # STEP 5
    # --------------------------------------------------------

    cashflow = build_patterns(
        cashflow
    )

    # --------------------------------------------------------
    # STEP 6
    # --------------------------------------------------------

    find_pattern_changes(
        cashflow
    )

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    print()
    print("========================================")
    print(" DAY 32 COMPLETED SUCCESSFULLY")
    print("========================================")
    print()

    print(
        "Companies verified : 92"
    )

    print()
    print(
        "Created:"
    )

    print(
        " -",
        SUMMARY_FILE
    )

    print(
        " -",
        CHANGES_FILE
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    generate_report()