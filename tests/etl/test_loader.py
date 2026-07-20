import sqlite3
import os

DB_PATH = "db/nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def test_database_exists():
    assert os.path.exists(DB_PATH)


def test_database_connection():
    conn = get_connection()
    assert conn is not None
    conn.close()


def test_companies_table_exists():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='companies';
    """)

    result = cursor.fetchone()

    conn.close()

    assert result is not None


def test_companies_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM companies;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count == 92


def test_balance_sheet_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM balancesheet;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count > 0


def test_analysis_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM analysis;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count > 0


def test_documents_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM documents;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count > 0


def test_prosandcons_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM prosandcons;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count > 0


def test_financial_ratios_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM financial_ratios;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count > 0


def test_market_cap_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM market_cap;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count > 0


def test_peer_groups_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM peer_groups;")

    count = cursor.fetchone()[0]

    conn.close()

    assert count > 0

def test_analysis_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM analysis;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 20

def test_analysis_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM analysis;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 21


def test_documents_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1586


def test_profitandloss_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM profitandloss;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1276


def test_cashflow_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cashflow;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1187


def test_financial_ratios_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM financial_ratios;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1184


def test_market_cap_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_cap;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 552


def test_stock_prices_row_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock_prices;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 5519    


