from fastapi import APIRouter
from app.utils.database import get_connection

router = APIRouter(
    prefix="/companies",
    tags=["Financials"]
)


@router.get("/{company_id}/ratios")
def get_ratios(company_id: str):
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            free_cash_flow_cr,
            capex_cr,
            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct,
            total_debt_cr,
            cash_from_operations_cr
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
    """, (company_id,)).fetchall()

    conn.close()

    return {
        "company_id": company_id,
        "count": len(rows),
        "ratios": [dict(row) for row in rows]
    }


@router.get("/{company_id}/cashflow")
def get_cashflow(company_id: str):
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
    """, (company_id,)).fetchall()

    conn.close()

    return {
        "company_id": company_id,
        "count": len(rows),
        "cashflow": [dict(row) for row in rows]
    }


@router.get("/{company_id}/profit-loss")
def get_profit_loss(company_id: str):
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            company_id,
            year,
            sales,
            expenses,
            operating_profit,
            opm_percentage,
            other_income,
            interest,
            depreciation,
            profit_before_tax,
            tax_percentage,
            net_profit,
            eps,
            dividend_payout
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
    """, (company_id,)).fetchall()

    conn.close()

    return {
        "company_id": company_id,
        "count": len(rows),
        "profit_loss": [dict(row) for row in rows]
    }