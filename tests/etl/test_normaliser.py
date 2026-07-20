import sqlite3

DB_PATH = "db/nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def count(query):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query)

    result = cursor.fetchone()[0]

    conn.close()

    return result


# -----------------------------
# Company Checks
# -----------------------------

def test_company_id_not_null():
    assert count(
        "SELECT COUNT(*) FROM companies WHERE id IS NULL"
    ) == 0


def test_company_name_not_null():
    assert count(
        "SELECT COUNT(*) FROM companies WHERE company_name IS NULL"
    ) == 0


def test_companies_has_rows():
    assert count(
        "SELECT COUNT(*) FROM companies"
    ) > 0


# -----------------------------
# Core Dataset Checks
# -----------------------------

def test_profitandloss_has_rows():
    assert count(
        "SELECT COUNT(*) FROM profitandloss"
    ) > 0


def test_balancesheet_has_rows():
    assert count(
        "SELECT COUNT(*) FROM balancesheet"
    ) > 0


def test_cashflow_has_rows():
    assert count(
        "SELECT COUNT(*) FROM cashflow"
    ) > 0


# -----------------------------
# Supporting Dataset Checks
# -----------------------------

def test_analysis_has_rows():
    assert count(
        "SELECT COUNT(*) FROM analysis"
    ) > 0


def test_documents_has_rows():
    assert count(
        "SELECT COUNT(*) FROM documents"
    ) > 0


def test_prosandcons_has_rows():
    assert count(
        "SELECT COUNT(*) FROM prosandcons"
    ) > 0


def test_financial_ratios_has_rows():
    assert count(
        "SELECT COUNT(*) FROM financial_ratios"
    ) > 0


def test_market_cap_has_rows():
    assert count(
        "SELECT COUNT(*) FROM market_cap"
    ) > 0


def test_peer_groups_has_rows():
    assert count(
        "SELECT COUNT(*) FROM peer_groups"
    ) > 0


def test_sectors_has_rows():
    assert count(
        "SELECT COUNT(*) FROM sectors"
    ) > 0


def test_stock_prices_has_rows():
    assert count(
        "SELECT COUNT(*) FROM stock_prices"
    ) > 0