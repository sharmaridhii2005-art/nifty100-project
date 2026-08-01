import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import run_query

st.set_page_config(
    page_title="Peer Comparison",
    layout="wide"
)

st.title("👥 Peer Comparison")

# =====================================
# Load Data
# =====================================

df = run_query("""
SELECT
    c.company_name,
    s.broad_sector,
    r.return_on_equity_pct,
    r.debt_to_equity,
    r.free_cash_flow_cr
FROM companies c
JOIN sectors s
    ON c.id = s.company_id
JOIN financial_ratios r
    ON c.id = r.company_id
WHERE r.year = 'Mar 2024'
""")

# =====================================
# Sidebar
# =====================================

sector = st.sidebar.selectbox(
    "Select Sector",
    sorted(df["broad_sector"].unique())
)

peers = df[df["broad_sector"] == sector]

company = st.sidebar.selectbox(
    "Select Company",
    peers["company_name"].tolist()
)

# =====================================
# Peer Table
# =====================================

st.subheader(f"Peer Companies - {sector}")

st.dataframe(
    peers[
        [
            "company_name",
            "return_on_equity_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

# =====================================
# ROE Chart
# =====================================

st.subheader("Return on Equity Comparison")

fig = px.bar(
    peers,
    x="company_name",
    y="return_on_equity_pct",
    color="company_name",
    text="return_on_equity_pct",
)

fig.update_layout(showlegend=False)

st.plotly_chart(
    fig,
    use_container_width=True,
)
# =====================================
# Debt / Equity Comparison
# =====================================

st.subheader("Debt / Equity Comparison")

fig = px.bar(
    peers,
    x="company_name",
    y="debt_to_equity",
    color="company_name",
    text="debt_to_equity",
)

fig.update_layout(showlegend=False)

st.plotly_chart(
    fig,
    use_container_width=True,
)

# =====================================
# Free Cash Flow Comparison
# =====================================

st.subheader("Free Cash Flow Comparison")

fig = px.bar(
    peers,
    x="company_name",
    y="free_cash_flow_cr",
    color="company_name",
    text="free_cash_flow_cr",
)

fig.update_layout(showlegend=False)

st.plotly_chart(
    fig,
    use_container_width=True,
)
