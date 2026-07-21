"""
Financial Ratio Engine
Sprint 2 - Day 08
"""
import sqlite3
import os
import logging



def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin = (Net Profit / Sales) * 100
    """
    if sales == 0:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin = Operating Profit / Sales × 100

    Returns None if operating profit or sales is missing.
    """

    if operating_profit is None:
        return None

    if sales is None or sales == 0:
        return None

    return (operating_profit / sales) * 100


def return_on_equity(net_profit, equity_capital, reserves):
    """
    Return on Equity (ROE)
    ROE = Net Profit / (Equity Capital + Reserves) * 100
    """
    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return (net_profit / total_equity) * 100


def return_on_capital_employed(ebit, equity_capital, reserves, borrowings):
    """
    Return on Capital Employed (ROCE)
    ROCE = EBIT / (Equity + Reserves + Borrowings) * 100
    """
    capital_employed = equity_capital + reserves + borrowings

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def return_on_assets(net_profit, total_assets):
    """
    Return on Assets (ROA)
    ROA = Net Profit / Total Assets * 100
    """
    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100

def debt_to_equity(borrowings, equity_capital, reserves):
    """
    Debt-to-Equity Ratio
    D/E = Borrowings / (Equity Capital + Reserves)
    """

    if borrowings == 0:
        return 0

    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return borrowings / total_equity

def high_leverage_flag(debt_to_equity_ratio, broad_sector):
    """
    High leverage if D/E > 5 and company is not in Financials.
    """

    if debt_to_equity_ratio is None:
        return False

    if broad_sector == "Financials":
        return False

    return debt_to_equity_ratio > 5


def interest_coverage_ratio(operating_profit, other_income, interest):
    """
    Interest Coverage Ratio =
    (Operating Profit + Other Income) / Interest

    Returns None if any required value is missing
    or interest is zero.
    """

    if operating_profit is None:
        return None

    if other_income is None:
        other_income = 0

    if interest is None or interest == 0:
        return None

    return (operating_profit + other_income) / interest
def icr_label(interest):
    """
    Label debt-free companies.
    """

    if interest == 0:
        return "Debt Free"

    return None

def icr_warning(icr):
    """
    Company may struggle to cover interest payments.
    """

    if icr is None:
        return False

    return icr < 1.5

def net_debt(borrowings, investments):
    """
    Net Debt = Borrowings - Investments
    """

    return borrowings - investments

def asset_turnover(sales, total_assets):
    """
    Asset Turnover = Sales / Total Assets
    """

    if total_assets == 0:
        return None

    return sales / total_assets