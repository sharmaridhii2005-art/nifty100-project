import sqlite3
import pandas as pd
import yaml

from src.screener.presets import *
from src.screener.scoring import calculate_score


class ScreenerEngine:

    def __init__(
        self,
        db_path="db/nifty100.db",
        config_path="config/screener_config.yaml"
    ):

        self.conn = sqlite3.connect(db_path)

        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)

    def load_data(self):

        # --------------------------
        # Financial Ratios
        # --------------------------
        fr = pd.read_sql(
            "SELECT * FROM financial_ratios",
            self.conn
        )

        fr = fr.drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )

        # Remove TTM rows
        fr = fr[fr["year"] != "TTM"].copy()

        # Extract numeric year
        fr["year_num"] = (
            fr["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        # --------------------------
        # Market Cap
        # --------------------------
        mc = pd.read_sql(
            "SELECT * FROM market_cap",
            self.conn
        )

        # Convert market cap year to integer
        if mc["year"].dtype == object:
            mc["year"] = (
                mc["year"]
                .astype(str)
                .str.extract(r"(\d{4})")[0]
                .astype(int)
            )

        df = fr.merge(
            mc,
            left_on=["company_id", "year_num"],
            right_on=["company_id", "year"],
            how="left"
        )

        # --------------------------
        # Profit & Loss
        # --------------------------
        pl = pd.read_sql(
    "SELECT * FROM profitandloss",
    self.conn
      )
        pl = pl.drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )

        # Remove TTM rows
        pl = pl[pl["year"] != "TTM"].copy()

        print("Columns before PL merge:")
        print(df.columns.tolist())

        df = df.merge(
            pl,
            left_on=["company_id", "year_x"],
            right_on=["company_id", "year"],
            how="left",
            suffixes=("", "_pl")
        )

        # --------------------------
        # Sector Table
        # --------------------------
        sectors = pd.read_sql(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector,
                market_cap_category
            FROM sectors
            """,
            self.conn
        )

        sectors = sectors.drop_duplicates(
            subset=["company_id"],
            keep="first"
        )

        df = df.merge(
            sectors,
            on="company_id",
            how="left"
        )

        return df
    
    def apply_filters(self):

        df = self.load_data()

        filters = self.config["filters"]

        # --------------------------
        # ROE
        # --------------------------
        if "roe_min" in filters:
            df = df[
                df["return_on_equity_pct"] >= filters["roe_min"]
            ]

        # --------------------------
        # Debt to Equity
        # --------------------------
        if "debt_to_equity_max" in filters:

            if "broad_sector" in df.columns:

                financials = (
                    df["broad_sector"] == "Financials"
                )

                non_financials = df[
                    (~financials)
                    &
                    (
                        df["debt_to_equity"]
                        <= filters["debt_to_equity_max"]
                    )
                ]

                df = pd.concat(
                    [
                        df[financials],
                        non_financials
                    ],
                    ignore_index=True
                )

            else:

                df = df[
                    df["debt_to_equity"]
                    <= filters["debt_to_equity_max"]
                ]

        # --------------------------
        # Free Cash Flow
        # --------------------------
        if "free_cash_flow_min" in filters:
            df = df[
                df["free_cash_flow_cr"]
                >= filters["free_cash_flow_min"]
            ]

        # --------------------------
        # Sales
        # --------------------------
        if "sales_min" in filters:
            df = df[
                df["sales"]
                >= filters["sales_min"]
            ]

        # --------------------------
        # Market Cap
        # --------------------------
        if "market_cap_min" in filters:
            df = df[
                df["market_cap_crore"]
                >= filters["market_cap_min"]
            ]

        # --------------------------
        # P/E
        # --------------------------
        if "pe_max" in filters:
            df = df[
                df["pe_ratio"]
                <= filters["pe_max"]
            ]

        # --------------------------
        # P/B
        # --------------------------
        if "pb_max" in filters:
            df = df[
                df["pb_ratio"]
                <= filters["pb_max"]
            ]

        # --------------------------
        # Dividend Yield
        # --------------------------
        if "dividend_yield_min" in filters:
            df = df[
                df["dividend_yield_pct"]
                >= filters["dividend_yield_min"]
            ]

        # --------------------------
        # Interest Coverage
        # --------------------------
        if "interest_coverage_min" in filters:

            df["interest_coverage"] = (
                df["interest_coverage"]
                .fillna(float("inf"))
            )

            df = df[
                df["interest_coverage"]
                >= filters["interest_coverage_min"]
            ]
         # --------------------------
        # Keep Latest Year Only FIRST
        # --------------------------
        df = (
            df.sort_values(
                ["company_id", "year_num"],
                ascending=[True, False]
            )
            .drop_duplicates(
                subset=["company_id"],
                keep="first"
            )
            .reset_index(drop=True)
        )

        # --------------------------
        # Calculate Composite Score
        # --------------------------
        df = calculate_score(df)

        # --------------------------
        # Sort by Score
        # --------------------------
        df = df.sort_values(
            "composite_quality_score",
            ascending=False
        )

        return df
    def apply_preset(self, preset):
        """
        Apply one of the predefined screener presets.
        """
        self.config["filters"] = preset
        return self.apply_filters()

    def run(self, preset=None):
        """
        Run the screener.
        """
        if preset is None:
            return self.apply_filters()

        return self.apply_preset(preset)
   