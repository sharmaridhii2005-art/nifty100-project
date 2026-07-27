"""
Cash Flow KPI Functions
Sprint 2 - Day 11
"""

def free_cash_flow(operating_activity, investing_activity):
    """
    Free Cash Flow = Operating Cash Flow + Investing Cash Flow

    Returns None if either value is missing.
    """

    if operating_activity is None or investing_activity is None:
        return None

    return operating_activity + investing_activity

def cfo_quality_score(cfo, pat):
    """
    CFO / PAT quality score

    > 1.0  -> High Quality
    0.5-1.0 -> Moderate
    < 0.5 -> Accrual Risk
    """

    if pat == 0:
        return "Accrual Risk"

    ratio = cfo / pat

    if ratio > 1:
        return "High Quality"

    elif ratio >= 0.5:
        return "Moderate"

    else:
        return "Accrual Risk"


def capex_intensity(investing_activity, sales):
    """
    Capex Intensity = |Investing Cash Flow| / Sales * 100

    Returns:
        (value, label)
    """

    if investing_activity is None or sales is None or sales == 0:
        return None, "N/A"

    value = (abs(investing_activity) / sales) * 100

    if value >= 10:
        label = "High"

    elif value >= 5:
        label = "Moderate"

    else:
        label = "Low"

    return round(value, 2), label

def fcf_conversion_rate(free_cash_flow_value, operating_profit):
    """
    FCF Conversion = FCF / Operating Profit * 100
    """

    if free_cash_flow_value is None:
        return None

    if operating_profit is None or operating_profit == 0:
        return None

    return (free_cash_flow_value / operating_profit) * 100


def capital_allocation_pattern(
    operating_activity,
    investing_activity,
    financing_activity,
    cfo_pat_ratio=None,
):
    """
    Classify capital allocation pattern.
    """

    if (
        operating_activity is None
        or investing_activity is None
        or financing_activity is None
    ):
        return None

    cfo = "+" if operating_activity >= 0 else "-"
    cfi = "+" if investing_activity >= 0 else "-"
    cff = "+" if financing_activity >= 0 else "-"

    pattern = (cfo, cfi, cff)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1:
            return "Shareholder Returns"
        return "Reinvestor"

    elif pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    elif pattern == ("-", "+", "+"):
        return "Distress Signal"

    elif pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    elif pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    elif pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    elif pattern == ("+", "-", "+"):
        return "Mixed"

    return "Unknown"