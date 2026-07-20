import os
import sqlite3
import pandas as pd

# -----------------------------
# Database Connection
# -----------------------------
os.makedirs("db", exist_ok=True)
conn = sqlite3.connect("db/nifty100.db")

# -----------------------------
# Create Output Folder
# -----------------------------
os.makedirs("output", exist_ok=True)

# -----------------------------
# Audit Report List
# -----------------------------
audit_data = []

# -----------------------------
# Folder Paths
# -----------------------------
raw_folder = "data/raw"
supp_folder = "data/supplementary"

# -----------------------------
# Core Dataset Files
# -----------------------------
raw_files = {
    "analysis": "analysis.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "companies": "companies.xlsx",
    "documents": "documents.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "prosandcons": "prosandcons.xlsx"
}

print("Loading Core Datasets...\n")

for table, filename in raw_files.items():

    path = os.path.join(raw_folder, filename)

    # These files have title row + header row
    if table in ["companies", "balancesheet", "cashflow", "profitandloss"]:
        df = pd.read_excel(path, header=1)
    else:
        df = pd.read_excel(path)

    df.to_sql(table, conn, if_exists="replace", index=False)

    print(f"{table} -> {len(df)} rows loaded")

    audit_data.append({
        "Table Name": table,
        "Rows Loaded": len(df),
        "Status": "Success"
    })

print("\nCore datasets loaded successfully.\n")

# -----------------------------
# Supporting Dataset Files
# -----------------------------
supp_files = {
    "financial_ratios": "financial_ratios.xlsx",
    "market_cap": "market_cap.xlsx",
    "peer_groups": "peer_groups.xlsx",
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx"
}

print("Loading Supporting Datasets...\n")

for table, filename in supp_files.items():

    path = os.path.join(supp_folder, filename)

    # These files have header in first row
    if table in [
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "sectors"
    ]:
        df = pd.read_excel(path, header=0)

    # stock_prices has title row
    else:
        df = pd.read_excel(path, header=1)

    df.to_sql(table, conn, if_exists="replace", index=False)

    print(f"{table} -> {len(df)} rows loaded")

    audit_data.append({
        "Table Name": table,
        "Rows Loaded": len(df),
        "Status": "Success"
    })

print("\nSupporting datasets loaded successfully.")

# -----------------------------
# Create Load Audit Report
# -----------------------------
audit_df = pd.DataFrame(audit_data)

audit_df.to_csv(
    "output/load_audit.csv",
    index=False
)

print("\nLoad Audit Report created successfully!")

print("\nAll datasets loaded into SQLite database successfully.")

conn.close()