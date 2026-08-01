import streamlit as st
from src.screener.engine import ScreenerEngine

st.set_page_config(
    page_title="Stock Screener",
    layout="wide"
)

st.title("🔍 Nifty 100 Stock Screener")

# Load Data
engine = ScreenerEngine()
df = engine.load_data()

# ---------------- Filters ----------------

st.sidebar.header("Filters")

roe = st.sidebar.slider(
    "Minimum ROE (%)",
    0.0,
    100.0,
    15.0
)

de = st.sidebar.slider(
    "Maximum Debt / Equity",
    0.0,
    5.0,
    1.0
)

fcf = st.sidebar.number_input(
    "Minimum Free Cash Flow",
    value=0.0
)

years = sorted(df["year"].dropna().unique())
year = st.sidebar.selectbox(
    "Financial Year",
    years
)

sectors = sorted(df["broad_sector"].dropna().unique())
sector = st.sidebar.selectbox(
    "Sector",
    ["All"] + sectors
)

filtered = df.copy()

filtered = filtered[
    filtered["return_on_equity_pct"] >= roe
]

filtered = filtered[
    filtered["debt_to_equity"] <= de
]

filtered = filtered[
    filtered["free_cash_flow_cr"] >= fcf
]

filtered = filtered[
    filtered["year"] == year
]
if sector != "All":
    filtered = filtered[
        filtered["broad_sector"] == sector
    ]

st.write(f"Companies Found: {len(filtered)}")
st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

# Create CSV
csv = filtered.to_csv(index=False).encode("utf-8")

# Download Button
st.download_button(
    "⬇ Download CSV",
    data=csv,
    file_name="screener_output.csv",
    mime="text/csv"
)