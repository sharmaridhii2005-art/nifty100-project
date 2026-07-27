import sqlite3
import pandas as pd
import numpy as np


class PeerEngine:

    def __init__(self, db_path="db/nifty100.db"):

        self.conn = sqlite3.connect(db_path)

    def load_data(self):

        ratios = pd.read_sql(
            "SELECT * FROM financial_ratios",
            self.conn
        )

        peers = pd.read_sql(
            "SELECT * FROM peer_groups",
            self.conn
        )

        return ratios, peers

    def latest_year(self, df):

        # Remove TTM rows
        df = df[df["year"] != "TTM"].copy()

        # Extract numeric year
        df["year_num"] = (
            df["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        # Keep latest year for each company
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

        return df

    def calculate_percentiles(self, df):

        # Metrics currently available in financial_ratios
        metrics = {
            "return_on_equity_pct": False,
            "net_profit_margin_pct": False,
            "debt_to_equity": True,      # Lower is better
            "free_cash_flow_cr": False,
            "interest_coverage": False,
            "asset_turnover": False,
        }

        results = []

        for peer_group, group in df.groupby("peer_group_name"):

            # Skip companies with no peer group
            if pd.isna(peer_group):
                continue

            for metric, inverse in metrics.items():

                temp = group[
                    [
                        "company_id",
                        "year",
                        "peer_group_name",
                        metric
                    ]
                ].copy()

                temp = temp.dropna()

                if temp.empty:
                    continue

                # Percentile ranking
                if inverse:
                    temp["percentile_rank"] = (
                        1 - temp[metric].rank(pct=True)
                    ) * 100
                else:
                    temp["percentile_rank"] = (
                        temp[metric].rank(pct=True)
                    ) * 100

                temp["metric"] = metric

                temp.rename(
                    columns={
                        metric: "value"
                    },
                    inplace=True
                )

                results.append(temp)

        if len(results) == 0:
            return pd.DataFrame()

        return pd.concat(
            results,
            ignore_index=True
        )

    def run(self):

        ratios, peers = self.load_data()

        ratios = self.latest_year(ratios)

        df = ratios.merge(
            peers,
            on="company_id",
            how="left"
        )

        percentiles = self.calculate_percentiles(df)

        # Save into SQLite
        percentiles.to_sql(
            "peer_percentiles",
            self.conn,
            if_exists="replace",
            index=False
        )

        print(
            f"Saved {len(percentiles)} percentile records to peer_percentiles table."
        )

        return percentiles