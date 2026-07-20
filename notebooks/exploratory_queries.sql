-- =========================================
-- Query 1: Total Companies
-- =========================================
SELECT COUNT(*) AS total_companies
FROM companies;

-- =========================================
-- Query 2: Top 10 Companies by Market Cap
-- =========================================
SELECT company_id,
       MAX(market_cap_crore) AS market_cap
FROM market_cap
GROUP BY company_id
ORDER BY market_cap DESC
LIMIT 10;

-- =========================================
-- Query 3: Top 10 Companies by Sales
-- =========================================
SELECT company_id,
       MAX(sales) AS highest_sales
FROM profitandloss
GROUP BY company_id
ORDER BY highest_sales DESC
LIMIT 10;

-- =========================================
-- Query 4: Top 10 Net Profit
-- =========================================
SELECT company_id,
       MAX(net_profit) AS net_profit
FROM profitandloss
GROUP BY company_id
ORDER BY net_profit DESC
LIMIT 10;

-- =========================================
-- Query 5: Highest Total Assets
-- =========================================
SELECT company_id,
       MAX(total_assets) AS assets
FROM balancesheet
GROUP BY company_id
ORDER BY assets DESC
LIMIT 10;

-- =========================================
-- Query 6: Highest Cash Flow
-- =========================================
SELECT company_id,
       MAX(net_cash_flow) AS cash_flow
FROM cashflow
GROUP BY company_id
ORDER BY cash_flow DESC
LIMIT 10;

-- =========================================
-- Query 7: Sector Wise Company Count
-- =========================================
SELECT broad_sector,
       COUNT(*) AS companies
FROM sectors
GROUP BY broad_sector
ORDER BY companies DESC;

-- =========================================
-- Query 8: Average ROE
-- =========================================
SELECT AVG(return_on_equity_pct) AS avg_roe
FROM financial_ratios;

-- =========================================
-- Query 9: Top Dividend Payout Companies
-- =========================================
SELECT company_id,
       MAX(dividend_payout_ratio_pct) AS dividend
FROM financial_ratios
GROUP BY company_id
ORDER BY dividend DESC
LIMIT 10;

-- =========================================
-- Query 10: Highest Debt Companies
-- =========================================
SELECT company_id,
       MAX(total_debt_cr) AS debt
FROM financial_ratios
GROUP BY company_id
ORDER BY debt DESC
LIMIT 10;