import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_pros_cons,
)
st.set_page_config(
    page_title="Company Profile",
    layout="wide"
)

st.title("🏢 Company Profile")

# ---------------------------------
# Load Companies
# ---------------------------------

companies = get_companies()

company_names = companies["company_name"].tolist()

selected_company = st.selectbox(
    "🔍 Search Company",
    company_names
)

company = companies[
    companies["company_name"] == selected_company
].iloc[0]

st.success(f"Selected Company: {company['company_name']}")

st.divider()

st.subheader("🏢 Company Information")

col1, col2 = st.columns([1, 3])

with col1:
    st.image(company["company_logo"], width=150)

with col2:
    st.markdown(f"### {company['company_name']}")

    st.write("**Company ID:**", company["id"])

    st.write("**Face Value:**", company["face_value"])

    st.write("**Book Value:**", company["book_value"])

    st.write("**ROE:**", company["roe_percentage"], "%")

    st.write("**ROCE:**", company["roce_percentage"], "%")

    st.write("**Website:**", company["website"])

st.divider()

st.subheader("📝 About Company")

st.write(company["about_company"])

st.divider()

st.subheader("📊 Financial KPIs")

from src.dashboard.utils.db import get_ratios

ratios = get_ratios(company["id"])

if ratios.empty:
    st.warning("No financial data available for this company.")
else:

    latest = ratios.sort_values("year").iloc[-1]

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric(
        "ROE",
        f"{latest['return_on_equity_pct']:.2f}%"
    )

    c2.metric(
        "ROCE",
        f"{company['roce_percentage']:.2f}%"
    )

    c3.metric(
        "Net Profit Margin",
        f"{latest['net_profit_margin_pct']:.2f}%"
    )

    c4.metric(
        "Debt / Equity",
        f"{latest['debt_to_equity']:.2f}"
    )

    c5.metric(
        "FCF",
        f"{latest['free_cash_flow_cr']:.2f} Cr"
    )

    c6.metric(
        "Asset Turnover",
        f"{latest['asset_turnover']:.2f}"
    )
    st.divider()

st.subheader("📈 Revenue & Net Profit (10 Years)")

pl = get_pl(company["id"])

if pl.empty:
    st.warning("No Profit & Loss data available.")
else:

    chart_df = pl.sort_values("year")

    fig = px.bar(
        chart_df,
        x="year",
        y=["sales", "net_profit"],
        barmode="group",
        title="Revenue vs Net Profit"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
    st.divider()

st.subheader("📉 ROE vs ROCE Trend")

ratios = get_ratios(company["id"])

if ratios.empty:
    st.warning("No ratio data available.")
else:

    ratios = ratios.sort_values("year")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=ratios["year"],
            y=ratios["return_on_equity_pct"],
            mode="lines+markers",
            name="ROE"
        )
    )

    # ROCE comes from companies table in your database,
    # so we use a constant value until yearly ROCE is available.
    fig.add_trace(
        go.Scatter(
            x=ratios["year"],
            y=[company["roce_percentage"]] * len(ratios),
            mode="lines+markers",
            name="ROCE"
        )
    )

    fig.update_layout(
        title="ROE vs ROCE",
        xaxis_title="Year",
        yaxis_title="Percentage",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)
    