import streamlit as st
import pandas as pd

from src.dashboard.utils.db import run_query

st.set_page_config(
    page_title="Reports",
    layout="wide"
)

st.title("📄 Reports & Export")

# =====================================
# Load Data
# =====================================

df = run_query("""
SELECT
    c.company_name,
    s.broad_sector,
    r.year,
    r.return_on_equity_pct,
    r.debt_to_equity,
    r.free_cash_flow_cr
FROM companies c
JOIN sectors s
    ON c.id = s.company_id
JOIN financial_ratios r
    ON c.id = r.company_id
WHERE r.year = 'Mar 2024'
ORDER BY c.company_name
""")

# =====================================
# Search Company
# =====================================

search = st.text_input("🔍 Search Company")

if search:
    df = df[df["company_name"].str.contains(search, case=False, na=False)]

st.write(f"Total Records: {len(df)}")

# =====================================
# Data Table
# =====================================

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# =====================================
# Download CSV
# =====================================

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download CSV",
    data=csv,
    file_name="nifty100_report.csv",
    mime="text/csv"
)