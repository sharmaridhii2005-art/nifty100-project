import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class RadarChartEngine:

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

        df = df[df["year"] != "TTM"].copy()

        df["year_num"] = (
            df["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        df = (
            df.sort_values(
                ["company_id", "year_num"],
                ascending=[True, False]
            )
            .drop_duplicates(
                subset="company_id",
                keep="first"
            )
        )

        return df

    def normalize(self, df, columns):

        temp = df.copy()

        for col in columns:

            if col not in temp.columns:
                continue

            minimum = temp[col].min()
            maximum = temp[col].max()

            if minimum == maximum:
                temp[col] = 50

            else:

                temp[col] = (
                    (temp[col] - minimum)
                    /
                    (maximum - minimum)
                ) * 100

        return temp

    def generate(self):

        ratios, peers = self.load_data()

        ratios = self.latest_year(ratios)

        df = ratios.merge(
            peers,
            on="company_id",
            how="left"
        )

        metrics = [
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
            "interest_coverage",
            "asset_turnover"
        ]

        df = self.normalize(df, metrics)

        os.makedirs(
            "reports/radar_charts",
            exist_ok=True
        )

        for peer_group, group in df.groupby("peer_group_name"):

            if pd.isna(peer_group):
                continue

            peer_average = (
                group[metrics]
                .mean()
                .tolist()
            )

            for _, row in group.iterrows():

                company_values = [
                    row[m]
                    for m in metrics
                ]

                labels = [
                    "ROE",
                    "NPM",
                    "D/E",
                    "FCF",
                    "ICR",
                    "AT"
                ]

                angles = np.linspace(
                    0,
                    2 * np.pi,
                    len(labels),
                    endpoint=False
                ).tolist()

                company_values += company_values[:1]
                peer_average_plot = peer_average + peer_average[:1]
                angles += angles[:1]

                fig = plt.figure(figsize=(7,7))

                ax = plt.subplot(
                    111,
                    polar=True
                )

                ax.plot(
                    angles,
                    company_values,
                    linewidth=2,
                    label=row["company_id"]
                )

                ax.fill(
                    angles,
                    company_values,
                    alpha=0.25
                )

                ax.plot(
                    angles,
                    peer_average_plot,
                    linestyle="--",
                    linewidth=2,
                    label="Peer Average"
                )

                ax.set_xticks(
                    angles[:-1]
                )

                ax.set_xticklabels(labels)

                ax.set_title(
                    row["company_id"],
                    fontsize=14
                )

                ax.legend(
                    loc="upper right"
                )

                plt.tight_layout()

                plt.savefig(
                    f"reports/radar_charts/{row['company_id']}_radar.png"
                )

                plt.close()

        print("Radar charts generated successfully.")