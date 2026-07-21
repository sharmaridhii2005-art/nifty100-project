from src.analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    icr_label,
    icr_warning,
    net_debt,
    asset_turnover,
)

def test_debt_to_equity_normal():
    assert debt_to_equity(500, 200, 300) == 1.0

def test_debt_to_equity_debt_free():
    assert debt_to_equity(0, 200, 300) == 0

def test_debt_to_equity_negative_equity():
    assert debt_to_equity(500, -200, 100) is None

def test_high_leverage_flag():
    assert high_leverage_flag(6.0, "Technology") is True

def test_interest_coverage_ratio():
    assert interest_coverage_ratio(1000, 100, 100) == 11.0

def test_icr_label():
    assert icr_label(0) == "Debt Free"

def test_net_debt():
    assert net_debt(500, 120) == 380

def test_asset_turnover():
    assert asset_turnover(1000, 500) == 2.0