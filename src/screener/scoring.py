import pandas as pd
import numpy as np


def winsorize(series):
    """
    Cap values between 10th and 90th percentile.
    """

    s = pd.to_numeric(series, errors="coerce")

    p10 = s.quantile(0.10)
    p90 = s.quantile(0.90)

    return s.clip(lower=p10, upper=p90)


def normalize(series):
    """
    Normalize values to 0-100.
    """

    s = winsorize(series)

    minimum = s.min()
    maximum = s.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(50, index=s.index)

    if maximum == minimum:
        return pd.Series(50, index=s.index)

    return ((s - minimum) / (maximum - minimum)) * 100


def calculate_score(df):

    df = df.copy()

    # -----------------------------
    # Profitability
    # -----------------------------

    roe = normalize(
        df["return_on_equity_pct"].fillna(0)
    )

    npm = normalize(
        df["net_profit_margin_pct"].fillna(0)
    )

    opm = normalize(
        df["operating_profit_margin_pct"].fillna(0)
    )

    # -----------------------------
    # Cash Quality
    # -----------------------------

    fcf = normalize(
        df["free_cash_flow_cr"].fillna(0)
    )

    cfo = normalize(
        df["cash_from_operations_cr"].fillna(0)
    )

    # -----------------------------
    # Growth
    # -----------------------------

    sales = normalize(
        df["sales"].fillna(0)
    )

    eps = normalize(
        df["earnings_per_share"].fillna(0)
    )

    # -----------------------------
    # Leverage
    # -----------------------------

    debt = 100 - normalize(
        df["debt_to_equity"].fillna(
            df["debt_to_equity"].median()
        )
    )

    icr = normalize(
        df["interest_coverage"].replace(
            np.inf,
            np.nan
        ).fillna(1000)
    )

    # -----------------------------
    # Composite Score
    # -----------------------------

    df["composite_quality_score"] = (

        roe * 0.15 +

        npm * 0.10 +

        opm * 0.10 +

        fcf * 0.15 +

        cfo * 0.10 +

        sales * 0.10 +

        eps * 0.10 +

        debt * 0.10 +

        icr * 0.10

    )

    df["composite_quality_score"] = (
        df["composite_quality_score"]
        .round(2)
    )

    return df