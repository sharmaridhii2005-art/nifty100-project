import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_dashboard_data,
    get_sectors,
    run_query,
)

st.set_page_config(
    page_title="Home",
    layout="wide",
)

st.title("🏠 Nifty 100 Analytics Dashboard")

# ======================================================
# Sidebar
# ======================================================

year_df = run_query("""
SELECT DISTINCT year
FROM financial_ratios
WHERE year LIKE 'Mar%'
ORDER BY year DESC
""")

years = year_df["year"].tolist()

year = st.sidebar.selectbox(
    "📅 Select Financial Year",
    years,
)

# ======================================================
# Load Data
# ======================================================

companies = get_companies()
dashboard = get_dashboard_data()
sectors = get_sectors()

ratios = dashboard[dashboard["year"] == year]

# ======================================================
# Debug (Remove later)
# ======================================================

st.info(f"Selected Year : {year}")
st.info(f"Rows Loaded : {len(ratios)}")

# ======================================================
# KPI Calculations
# ======================================================

total_companies = len(companies)

if ratios.empty:
    avg_roe = 0
    median_de = 0
    debt_free = 0
else:
    avg_roe = round(
        ratios["return_on_equity_pct"].mean(),
        2,
    )

    median_de = round(
        ratios["debt_to_equity"].median(),
        2,
    )

    debt_free = (
        ratios["debt_to_equity"] <= 0
    ).sum()

# ======================================================
# Median P/E
# ======================================================

pe_df = run_query("""
SELECT year, pe_ratio
FROM market_cap
""")

pe_data = pe_df[
    pe_df["year"] == year
]

if pe_data.empty:
    median_pe = 0
else:
    median_pe = round(
        pe_data["pe_ratio"].median(),
        2,
    )

# Placeholder until CAGR module is added

median_revenue_cagr = "N/A"

# ======================================================
# KPI Cards
# ======================================================

st.subheader("📊 Dashboard Summary")

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric(
    "Companies",
    total_companies,
)

c2.metric(
    "Average ROE",
    f"{avg_roe}%",
)

c3.metric(
    "Median P/E",
    median_pe,
)

c4.metric(
    "Median D/E",
    median_de,
)

c5.metric(
    "Revenue CAGR",
    median_revenue_cagr,
)

c6.metric(
    "Debt-Free",
    debt_free,
)

st.divider()

# ======================================================
# Sector Distribution
# ======================================================

st.subheader("🏭 Sector Distribution")

sector_counts = (
    sectors.groupby("broad_sector")
    .size()
    .reset_index(name="Companies")
)

fig = px.pie(
    sector_counts,
    names="broad_sector",
    values="Companies",
    hole=0.45,
    title="Nifty 100 Sector Distribution",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

st.divider()

# ======================================================
# Top Companies
# ======================================================

st.subheader("🏆 Top 5 Companies by ROE")

top = (
    ratios.sort_values(
        "return_on_equity_pct",
        ascending=False,
    )
    .head(5)
)

top = top[
    [
        "company_name",
        "broad_sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
    ]
]

st.dataframe(
    top,
    use_container_width=True,
    hide_index=True,
)