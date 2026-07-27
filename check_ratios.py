import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

df = pd.read_sql("""
SELECT
company_id,
year,
return_on_equity_pct,
operating_profit_margin_pct,
net_profit_margin_pct
FROM financial_ratios
WHERE company_id IN ('HINDUNILVR','HAL')
""", conn)

print(df)

conn.close()