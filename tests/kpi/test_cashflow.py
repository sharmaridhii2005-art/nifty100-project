from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
)


def test_free_cash_flow():
    assert free_cash_flow(1000, -300) == 700


def test_cfo_quality_high():
    assert cfo_quality_score(120, 100) == "High Quality"


def test_cfo_quality_moderate():
    assert cfo_quality_score(70, 100) == "Moderate"


def test_cfo_quality_risk():
    assert cfo_quality_score(30, 100) == "Accrual Risk"


def test_capex_intensity():
    value, label = capex_intensity(-50, 1000)
    assert value == 5.0
    assert label == "Moderate"


def test_fcf_conversion():
    assert fcf_conversion_rate(700, 1000) == 70.0