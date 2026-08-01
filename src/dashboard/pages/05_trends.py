import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_pl,
)

st.set_page_config(
    page_title="Company Trends",
    layout="wide"
)

st.title("📈 Company Financial Trends")

# -----------------------------
# Load Companies
# -----------------------------

companies = get_companies()

company_name = st.sidebar.selectbox(
    "Select Company",
    companies["company_name"]
)

company = companies[
    companies["company_name"] == company_name
].iloc[0]

pl = get_pl(company["id"])

if pl.empty:
    st.warning("No financial data available.")
    st.stop()

st.subheader(company_name)

# Revenue Trend
st.subheader("Revenue Trend")

fig = px.line(
    pl,
    x="year",
    y="sales",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# Net Profit Trend
st.subheader("Net Profit Trend")

fig = px.line(
    pl,
    x="year",
    y="net_profit",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# EPS Trend
st.subheader("EPS Trend")

fig = px.line(
    pl,
    x="year",
    y="eps",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# Operating Profit Margin Trend
st.subheader("Operating Profit Margin")

fig = px.line(
    pl,
    x="year",
    y="opm_percentage",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)