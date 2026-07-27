import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

df = pd.read_sql("""
SELECT
company_id,
year,
sales,
operating_profit,
opm_percentage,
net_profit
FROM profitandloss
WHERE company_id IN ('HINDUNILVR','HAL')
""", conn)

print(df)

conn.close()