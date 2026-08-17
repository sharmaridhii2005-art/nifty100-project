import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Nifty 100 Analytics Dashboard")
st.write("Company analytics powered by FastAPI")


# -----------------------------
# Health check
# -----------------------------
try:
    health = requests.get(
        f"{API}/health",
        timeout=5
    ).json()

    st.success(
        f"API Status: {health.get('status', 'unknown')}"
    )

except Exception:
    st.error("FastAPI server is not running.")
    st.stop()


# -----------------------------
# Load companies
# -----------------------------
try:
    response = requests.get(
        f"{API}/companies",
        timeout=10
    )
    response.raise_for_status()

    companies_data = response.json()

    if isinstance(companies_data, list):
        companies = [
            company
            for company in companies_data
            if isinstance(company, dict)
        ]

    elif isinstance(companies_data, dict):
        companies = companies_data.get("companies", [])

        if not isinstance(companies, list):
            companies = []

    else:
        companies = []

except Exception as e:
    st.error(f"Unable to load companies: {e}")
    st.stop()


# -----------------------------
# Company selector
# -----------------------------
company_options = {
    company["id"]: company.get(
        "company_name",
        company["id"]
    )
    for company in companies
    if "id" in company
}

if not company_options:
    st.error("No companies were returned by the API.")
    st.stop()

selected = st.selectbox(
    "Select Company",
    options=list(company_options.keys()),
    format_func=lambda x: f"{x} - {company_options[x]}"
)


# -----------------------------
# Company Summary
# -----------------------------
if selected:

    response = requests.get(
        f"{API}/companies/{selected}/summary",
        timeout=10
    )

    if response.status_code != 200:
        st.error("Unable to load company summary.")
        st.stop()

    data = response.json()

    company = data.get("company") or {}
    sector = data.get("sector") or {}
    ratio = data.get("latest_ratio") or {}
    cluster = data.get("cluster") or {}
    valuation = data.get("valuation") or {}


    # -----------------------------
    # Company name
    # -----------------------------
    st.header(
        company.get(
            "company_name",
            selected
        )
    )


    # -----------------------------
    # KPI cards
    # -----------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "ROE",
        f"{company.get('roe_percentage', 0):.2f}%"
    )

    col2.metric(
        "ROCE",
        f"{company.get('roce_percentage', 0):.2f}%"
    )

    col3.metric(
        "Debt / Equity",
        f"{ratio.get('debt_to_equity', 0):.2f}"
    )

    col4.metric(
        "Operating Margin",
        f"{ratio.get('operating_profit_margin_pct', 0):.2f}%"
    )


    # -----------------------------
    # Company Information
    # -----------------------------
    st.subheader("Company Information")

    info_col1, info_col2 = st.columns(2)

    with info_col1:

        st.write(
            "**Sector:**",
            sector.get("broad_sector", "N/A")
        )

        st.write(
            "**Sub-sector:**",
            sector.get("sub_sector", "N/A")
        )

        st.write(
            "**Market Cap:**",
            sector.get("market_cap_category", "N/A")
        )

    with info_col2:

        st.write(
            "**Book Value:**",
            company.get("book_value", "N/A")
        )

        st.write(
            "**Index Weight:**",
            sector.get("index_weight_pct", "N/A")
        )

        st.write(
            "**Latest Financial Year:**",
            ratio.get("year", "N/A")
        )


    # -----------------------------
    # Cluster Analysis
    # -----------------------------
    st.subheader("Cluster Analysis")

    if cluster:

        st.info(
            f"Cluster: **{cluster.get('cluster_name', 'N/A')}**"
        )

        st.write(
            "Distance from centroid:",
            cluster.get(
                "distance_from_centroid",
                "N/A"
            )
        )

    else:
        st.warning("No cluster information available.")


    # -----------------------------
    # Valuation
    # -----------------------------
    st.subheader("Valuation")

    if valuation:

        v1, v2, v3, v4 = st.columns(4)

        v1.metric(
            "P/E",
            valuation.get("P/E", "N/A")
        )

        v2.metric(
            "P/B",
            valuation.get("P/B", "N/A")
        )

        v3.metric(
            "EV/EBITDA",
            valuation.get("EV/EBITDA", "N/A")
        )

        v4.metric(
            "FCF Yield",
            f"{valuation.get('FCF_yield_pct', 0):.2f}%"
        )

        st.write(
            "**Valuation Flag:**",
            valuation.get("flag", "N/A")
        )

        st.write(
            "**P/E vs Sector Median:**",
            f"{valuation.get('PE_vs_sector_median_pct', 0):.2f}%"
        )

    else:
        st.warning("No valuation information available.")


    # -----------------------------
    # Outliers
    # -----------------------------
    st.subheader("Outlier Analysis")

    outliers = data.get("outliers", [])

    if outliers:

        st.dataframe(
            pd.DataFrame(outliers),
            use_container_width=True
        )

    else:

        st.success(
            "No outliers detected for this company."
        )