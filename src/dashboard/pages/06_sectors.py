import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import run_query

st.set_page_config(
    page_title="Sector Analysis",
    layout="wide"
)

st.title("🏭 Sector Analysis")

# Load Data

df = run_query("""
SELECT
    s.broad_sector,
    AVG(r.return_on_equity_pct) AS avg_roe,
    AVG(r.debt_to_equity) AS avg_de,
    AVG(r.free_cash_flow_cr) AS avg_fcf
FROM financial_ratios r
JOIN sectors s
    ON r.company_id = s.company_id
WHERE r.year = 'Mar 2024'
GROUP BY s.broad_sector
ORDER BY s.broad_sector
""")

st.subheader("Average ROE by Sector")

fig = px.bar(
    df,
    x="broad_sector",
    y="avg_roe",
    color="broad_sector",
    text="avg_roe",
)

fig.update_layout(showlegend=False)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.subheader("Average Debt / Equity")

fig = px.bar(
    df,
    x="broad_sector",
    y="avg_de",
    color="broad_sector",
    text="avg_de",
)

fig.update_layout(showlegend=False)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.subheader("Average Free Cash Flow")

fig = px.bar(
    df,
    x="broad_sector",
    y="avg_fcf",
    color="broad_sector",
    text="avg_fcf",
)

fig.update_layout(showlegend=False)

st.plotly_chart(
    fig,
    use_container_width=True
)