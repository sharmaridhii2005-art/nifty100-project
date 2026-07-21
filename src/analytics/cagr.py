"""
CAGR Engine
Sprint 2 - Day 10
"""

from math import pow


def calculate_cagr(start_value, end_value, years):
    """
    CAGR = ((End / Start) ** (1 / Years) - 1) * 100

    Returns:
        (cagr_value, flag)
    """

    if years <= 0:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    cagr = (pow(end_value / start_value, 1 / years) - 1) * 100

    return round(cagr, 2), None