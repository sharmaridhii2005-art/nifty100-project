from src.screener.engine import ScreenerEngine

engine = ScreenerEngine()

df = engine.run()

print(df[
    [
        "company_id",
        "year_x",
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "composite_quality_score"
    ]
].head(10))