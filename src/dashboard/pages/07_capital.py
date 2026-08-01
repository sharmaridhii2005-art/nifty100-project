import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import run_query

st.set_page_config(
    page_title="Capital Analysis",
    layout="wide"
)

st.title("💰 Capital Market Analysis")

# ==========================================
# Load Data
# ==========================================

df = run_query("""
SELECT
    c.company_name,
    s.broad_sector,
    m.year,
    m.market_cap_crore,
    m.enterprise_value_crore,
    m.pe_ratio,
    m.pb_ratio,
    m.ev_ebitda,
    m.dividend_yield_pct
FROM market_cap m
JOIN companies c
    ON m.company_id = c.id
JOIN sectors s
    ON c.id = s.company_id
WHERE m.year = 2024
ORDER BY m.market_cap_crore DESC
""")

if df.empty:
    st.warning("No Market Capitalization data found.")
    st.stop()

# ==========================================
# Sidebar
# ==========================================

sector = st.sidebar.selectbox(
    "Select Sector",
    ["All"] + sorted(df["broad_sector"].dropna().unique())
)

if sector != "All":
    df = df[df["broad_sector"] == sector]

# ==========================================
# KPI Cards
# ==========================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Companies",
    len(df)
)

c2.metric(
    "Average P/E",
    f"{df['pe_ratio'].mean():.2f}"
)

c3.metric(
    "Average P/B",
    f"{df['pb_ratio'].mean():.2f}"
)

c4.metric(
    "Average Dividend Yield",
    f"{df['dividend_yield_pct'].mean():.2f}%"
)

st.divider()

# ==========================================
# Market Cap Chart
# ==========================================

st.subheader("Top 15 Companies by Market Capitalization")

fig = px.bar(
    df.sort_values(
        "market_cap_crore",
        ascending=False
    ).head(15),
    x="company_name",
    y="market_cap_crore",
    color="broad_sector",
    text="market_cap_crore",
)

fig.update_layout(
    xaxis_title="Company",
    yaxis_title="Market Cap (₹ Cr)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# P/E Ratio Chart
# ==========================================

st.subheader("P/E Ratio Comparison")

fig = px.bar(
    df.sort_values(
        "pe_ratio",
        ascending=False
    ).head(15),
    x="company_name",
    y="pe_ratio",
    color="broad_sector",
    text="pe_ratio",
)

fig.update_layout(
    xaxis_title="Company",
    yaxis_title="P/E Ratio"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# P/B Ratio Chart
# ==========================================

st.subheader("P/B Ratio Comparison")

fig = px.bar(
    df.sort_values(
        "pb_ratio",
        ascending=False
    ).head(15),
    x="company_name",
    y="pb_ratio",
    color="broad_sector",
    text="pb_ratio",
)

fig.update_layout(
    xaxis_title="Company",
    yaxis_title="P/B Ratio"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# Dividend Yield Chart
# ==========================================

st.subheader("Dividend Yield Comparison")

fig = px.bar(
    df.sort_values(
        "dividend_yield_pct",
        ascending=False
    ).head(15),
    x="company_name",
    y="dividend_yield_pct",
    color="broad_sector",
    text="dividend_yield_pct",
)

fig.update_layout(
    xaxis_title="Company",
    yaxis_title="Dividend Yield (%)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# Data Table
# ==========================================

st.subheader("Market Valuation Table")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# Download CSV
# ==========================================

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download Capital Report",
    data=csv,
    file_name="capital_analysis_2024.csv",
    mime="text/csv"
)