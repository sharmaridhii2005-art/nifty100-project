import os
import sqlite3
import pandas as pd


def generate_valuation():

    # -------------------------------
    # Project paths
    # -------------------------------

    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )

    market_cap_path = os.path.join(
        BASE_DIR,
        "data",
        "supplementary",
        "market_cap.xlsx"
    )

    db_path = os.path.join(
        BASE_DIR,
        "db",
        "nifty100.db"
    )

    output_dir = os.path.join(
        BASE_DIR,
        "output"
    )

    os.makedirs(output_dir, exist_ok=True)


    # -------------------------------
    # Load market valuation data
    # -------------------------------

    market_df = pd.read_excel(
        market_cap_path
    )


    # -------------------------------
    # Load database data
    # -------------------------------

    conn = sqlite3.connect(db_path)


    financial_df = pd.read_sql(
        """
        SELECT *
        FROM financial_ratios
        """,
        conn
    )


    company_df = pd.read_sql(
        """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        """,
        conn
    )


    sector_df = pd.read_sql(
        """
        SELECT
            company_id,
            broad_sector AS sector,
            sub_sector
        FROM sectors
        """,
        conn
    )


    conn.close()


    # -------------------------------
    # Add company information
    # -------------------------------

    financial_df = financial_df.merge(
        company_df,
        on="company_id",
        how="left"
    )


    financial_df = financial_df.merge(
        sector_df,
        on="company_id",
        how="left"
    )


    # -------------------------------
    # Fix year columns
    # -------------------------------

    financial_df["year"] = (
        financial_df["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
    )


    market_df["year"] = (
        market_df["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
    )


    # Remove invalid years

    financial_df = financial_df[
        financial_df["year"].notna()
    ]

    market_df = market_df[
        market_df["year"].notna()
    ]


    financial_df["year"] = (
        financial_df["year"]
        .astype(int)
    )


    market_df["year"] = (
        market_df["year"]
        .astype(int)
    )


    # -------------------------------
    # Merge financial + valuation
    # -------------------------------

    df = financial_df.merge(
        market_df,
        on=[
            "company_id",
            "year"
        ],
        how="left"
    )


    # -------------------------------
    # Calculate FCF Yield
    # -------------------------------

    df["FCF_yield_pct"] = (
        df["free_cash_flow_cr"]
        /
        df["market_cap_crore"]
    ) * 100


    df["FCF_yield_pct"] = (
        df["FCF_yield_pct"]
        .replace(
            [float("inf"), -float("inf")],
            None
        )
    )


    # -------------------------------
    # Latest available year
    # -------------------------------

    latest = (
        df.sort_values("year")
        .groupby("company_id")
        .tail(1)
    )


    # -------------------------------
    # Sector median PE
    # -------------------------------

    sector_median = (
        latest
        .groupby("sector")["pe_ratio"]
        .median()
        .reset_index()
    )


    sector_median.rename(
        columns={
            "pe_ratio":
            "5yr_median_PE"
        },
        inplace=True
    )


    latest = latest.merge(
        sector_median,
        on="sector",
        how="left"
    )


    # -------------------------------
    # PE comparison
    # -------------------------------

    latest["PE_vs_sector_median_pct"] = (

        (
            latest["pe_ratio"]
            -
            latest["5yr_median_PE"]
        )
        /
        latest["5yr_median_PE"]

    ) * 100



    # -------------------------------
    # Valuation classification
    # -------------------------------

    def valuation_flag(row):

        if pd.isna(row["5yr_median_PE"]):
            return "Fair"

        if row["pe_ratio"] > (
            row["5yr_median_PE"] * 1.5
        ):
            return "Caution"


        elif row["pe_ratio"] < (
            row["5yr_median_PE"] * 0.7
        ):
            return "Discount"


        else:
            return "Fair"



    latest["flag"] = latest.apply(
        valuation_flag,
        axis=1
    )


    # -------------------------------
    # Final output
    # -------------------------------

    result = latest[
        [
            "company_id",
            "company_name",
            "sector",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag"
        ]
    ]


    result.rename(
        columns={
            "pe_ratio":"P/E",
            "pb_ratio":"P/B",
            "ev_ebitda":"EV/EBITDA"
        },
        inplace=True
    )


    # -------------------------------
    # Save Excel
    # -------------------------------

    excel_path = os.path.join(
        output_dir,
        "valuation_summary.xlsx"
    )


    result.to_excel(
        excel_path,
        index=False
    )


    # -------------------------------
    # Save flagged companies
    # -------------------------------

    flags = result[
        result["flag"].isin(
            [
                "Caution",
                "Discount"
            ]
        )
    ]


    csv_path = os.path.join(
        output_dir,
        "valuation_flags.csv"
    )


    flags.to_csv(
        csv_path,
        index=False
    )


    print("--------------------------------")
    print(" Valuation Completed Successfully ")
    print("--------------------------------")
    print(
        "Companies generated:",
        len(result)
    )
    print(
        "Created:",
        excel_path
    )
    print(
        "Created:",
        csv_path
    )



if __name__ == "__main__":
    generate_valuation()