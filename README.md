# Nifty 100 Analytics Dashboard

## Overview

Nifty 100 Analytics Dashboard is a Streamlit-based financial analytics application that provides company analysis, stock screening, peer comparison, trend analysis, sector insights, capital allocation visualization, annual report access, and valuation analysis for 92 Nifty 100 companies.

---

## Features

- Dashboard Overview
- Company Profile
- Stock Screener
- Peer Comparison
- Trend Analysis
- Sector Analysis
- Capital Allocation Map
- Annual Reports
- Valuation Module

---

## Technologies Used

- Python
- Streamlit
- Pandas
- Plotly
- SQLite
- OpenPyXL

---

## Project Structure

```
nifty100-project
│
├── src
│   ├── analytics
│   ├── dashboard
│   ├── screener
│   └── etl
│
├── db
├── data
├── output
└── README.md
```

---

## Installation

### Clone repository

```bash
git clone <repository-url>
cd nifty100-project
```

### Create virtual environment

```bash
python -m venv venv
```

### Activate

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

### Install requirements

```bash
pip install -r requirements.txt
```

---

## Run Dashboard

```bash
streamlit run src/dashboard/app.py
```

Dashboard URL

```
http://localhost:8501
```

---

## Dashboard Screens

### Home
- Summary KPIs
- Sector distribution
- Top quality companies

### Company Profile
- Financial KPIs
- Revenue & Profit charts
- ROE & ROCE trends
- Pros & Cons

### Screener
- Metric filters
- Preset filters
- CSV export

### Peer Comparison
- Radar chart
- KPI comparison

### Trend Analysis
- Multi-metric trends
- YoY analysis

### Sector Analysis
- Bubble chart
- Sector KPIs

### Capital Allocation
- Treemap visualization

### Annual Reports
- Company-wise report links

---

## Valuation Module

Generates:

- output/valuation_summary.xlsx
- output/valuation_flags.csv

Calculations:

- FCF Yield
- Sector Median P/E
- Valuation Flag (Fair, Discount, Caution)

---

## Outputs

- peer_comparison.xlsx
- screener_output.xlsx
- valuation_summary.xlsx
- valuation_flags.csv

---

## Author

Ridhi Sharma